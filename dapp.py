import json
import logging

from cartesi import ABIRouter, DApp, JSONRouter, Rollup, RollupData, abi
from cartesi.router import DAppAddressRouter
from cartesi.vouchers import create_voucher_from_model
from pydantic import BaseModel

from auction import (Auction, Bid, Operation, aggregate_vouchers,
                     auction_output, auction_price, auction_vouchers)

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ADDRESS_RELAY_ADDRESS = "0xf5de34d6bbc0446e2a45719e718efebaae179dae"
ERC20_PORTAL = "0x9C21AEb2093C32DDbC53eEF24B873BDCd1aDa1DB"
TOKEN_ADDRESS = "0x"

dapp = DApp()
json_router = JSONRouter()
dapp_address = DAppAddressRouter(relay_address=ADDRESS_RELAY_ADDRESS)
abi_router = ABIRouter()

dapp.add_router(json_router)
dapp.add_router(dapp_address)
dapp.add_router(abi_router)

# This dapp will read and write from this global state dict
state: list[Auction] = []


def str2hex(str):
    """Encodes a string as a hex string"""
    return "0x" + str.encode("utf-8").hex()


def to_jsonhex(data):
    """Encode as a JSON hex"""
    return str2hex(json.dumps(data))


def state2hex(data):
    return "0x" + str(data).encode("utf-8").hex()


# Example Json:
# {
#    "op": "new-auction",
#    "end_time": 100,
#    "lock_time": 200,
#    "reserve_price": 7000,
#    "volume_limit": 2000,
# }
@json_router.advance({"op": "new-auction"})
def handle_new_auction(rollup: Rollup, data: RollupData):
    auction_data = data.json_payload()
    state.append(
        Auction(
            int(auction_data["end_time"] + data.metadata.timestamp),
            int(auction_data["lock_time"]),
            int(auction_data["volume_limit"]),
            int(auction_data["reserve_price"]),
            [],
        )
    )

    rollup.report(state2hex(state))
    return True


class TransferArgs(BaseModel):
    _to: abi.Address
    _amount: abi.UInt256
    _ts: abi.UInt256


class MintArgs(BaseModel):
    _to: abi.Address
    _amount: abi.UInt256
    _ts: abi.UInt256


class BurnArgs(BaseModel):
    _from: abi.Address
    _amount: abi.UInt256
    _ts: abi.UInt256


# Example Json:
# {
#    "op": "end-auction",
#    "id": 0,
# }
@json_router.advance({"op": "end-auction"})
def handle_end_auction(rollup: Rollup, data: RollupData):
    if dapp_address.address is None:
        return False
    payload = data.json_payload()
    index = payload["id"]
    auction = state[index]

    if data.metadata.timestamp < auction.end_time:
        return

    output = auction_output(auction.bids, auction.volume_limit)
    price = auction_price(output)
    vouchers = auction_vouchers(output.bid_outputs, price)
    aggregated_vouchers = aggregate_vouchers(vouchers)
    for v in aggregated_vouchers:
        lock_timestamp = (
            data.metadata.timestamp + auction.lock_time * v.timestamp_locked
        )
        if v.op == Operation.BURN:
            voucher = create_voucher_from_model(
                destination=TOKEN_ADDRESS,
                function_name="burnAfterTimestamp",
                args_model=BurnArgs(
                    _from=dapp_address.address, _amount=v.amount, _ts=lock_timestamp
                ),
            )
        if v.op == Operation.MINT:
            voucher = create_voucher_from_model(
                destination=TOKEN_ADDRESS,
                function_name="mintAfterTimestamp",
                args_model=MintArgs(_to=v.user, _amount=v.amount, _ts=lock_timestamp),
            )
        if v.op == Operation.TRANSFER:
            voucher = create_voucher_from_model(
                destination=TOKEN_ADDRESS,
                function_name="transferAfterTimestamp",
                args_model=TransferArgs(
                    _to=v.user, _amount=v.amount, _ts=lock_timestamp
                ),
            )
        rollup.voucher(voucher)

    return True


class DepositErc20Payload(BaseModel):
    token: abi.Address
    sender: abi.Address
    depositAmount: abi.UInt256
    execLayerData: bytes


class ExecLayerPayload(BaseModel):
    auction_id: abi.UInt256
    price: abi.UInt256


@abi_router.advance(msg_sender=ERC20_PORTAL)
def new_bid(rollup: Rollup, data: RollupData):
    payload = data.bytes_payload()
    LOGGER.debug("Payload: %s", payload.hex())

    deposit = abi.decode_to_model(data=payload, model=DepositErc20Payload, packed=True)
    execData = abi.decode_to_model(data=deposit.execLayerData, model=ExecLayerPayload)
    if deposit.token == TOKEN_ADDRESS:
        bidder = deposit.sender.lower()
        volume = deposit.depositAmount
        price = execData.price
        auction_id = execData.auction_id

        bid = Bid(data.metadata.timestamp, volume, price, bidder)
        state[auction_id].new_bid(bid)

    return True


@json_router.inspect({"op": "get"})
def handle_inspect_get(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    index = int(data['key'])
    LOGGER.debug("Index: %s", index)

    try:
            rollup.report(to_jsonhex({'key': index, 'value': state[index]}))
    except:
            rollup.report(to_jsonhex({'key': index, 'error': 'not found'}))

    return True


if __name__ == "__main__":
    dapp.run()
