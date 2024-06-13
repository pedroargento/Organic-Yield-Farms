import json
import logging
from typing import Dict

from cartesi import DApp, JSONRouter, Rollup, RollupData, ABIRouter
from cartesi.router import DAppAddressRouter

from auction import *

LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

ADDRESS_RELAY_ADDRESS = "0xf5de34d6bbc0446e2a45719e718efebaae179dae"

dapp = DApp()
json_router = JSONRouter()
dapp_address = DAppAddressRouter(relay_address=ADDRESS_RELAY_ADDRESS)
abi_router = ABIRouter()

dapp.add_router(json_router)
dapp.add_router(dapp_address)
dapp.add_router(abi_router)

ERC20_PORTAL = "0x9C21AEb2093C32DDbC53eEF24B873BDCd1aDa1DB"
# This dapp will read and write from this global state dict
state: dict[str, Auction] = {}


def str2hex(str):
    """Encodes a string as a hex string"""
    return "0x" + str.encode("utf-8").hex()


def to_jsonhex(data):
    """Encode as a JSON hex"""
    return str2hex(json.dumps(data))


# Example Json:
# {
#    "op": "new-auction",
#    "id": "key_1",
#    "end_time": 100,
#    "lock_time": 200,
#    "reserve_price": 7000,
#    "volume_limit": 2000,
# }
@json_router.advance({"op": "new-auction"})
def handle_new_auction(rollup: Rollup, data: RollupData):
    metadata = data["metadata"]
    auction_data = data.json_payload()
    key = auction_ata["id"]
    state[key] = Auction(
        int(auction_data["end_time"] + metadata["timestamp"]),
        int(auction_data["lock_time"] + metadata["timestamp"]),
        int(auction_data["volume_limit"]),
        int(auction_data["reserve_price"]),
        [],
    )

    rollup.report(to_jsonhex(state))
    return True
# Example Json:
# {
#    "op": "end-auction",
#    "id": "key_1",
# }
@json_router.advance({"op": "end-auction"})
def handle_new_auction(rollup: Rollup, data: RollupData):
    metadata = data["metadata"]
    auction_data = data.json_payload()
    key = dauction_ata["id"]
    auction=state[key]

    output = auction_output(auction.bids, auction.volume_limit)
    price = auction_price(output)
    vouchers = auction_vouchers(output.bid_outputs, price)
    aggregated_vouchers = aggregate_vouchers(vouchers)
    rollup.report(to_jsonhex(state))
    return True

@abi_router.advance(msg_sender=ERC20_PORTAL)
def new_bid(rollup: Rollup, data: RollupData):
    pass

@json_router.inspect({"op": "get"})
def handle_inspect_get(rollup: Rollup, data: RollupData):
    data = data.json_payload()
    rollup.report(to_jsonhex(state))

    return True


if __name__ == "__main__":
    dapp.run()
