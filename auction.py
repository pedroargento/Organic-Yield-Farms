from collections.abc import Iterable
from enum import IntEnum
from itertools import accumulate, chain, groupby, starmap
from typing import NamedTuple, NewType

Address = NewType("Address", str)
PRICE_DECIMALS = 10000


class Bid(NamedTuple):
    timestamp: int
    volume: int
    price: int
    bidder: Address


class Auction(NamedTuple):
    end_time: int
    lock_time: int
    volume_limit: int
    reserve_price: int
    bids: list[Bid]

    def new_bid(self, bid: Bid):
        if bid.timestamp <= self.end_time and bid.price >= self.reserve_price:
            self.bids.append(bid)
        else:
            raise ValueError("invalid bid")


class BidOutput(NamedTuple):
    bidder: Address
    amount_sent: int
    amount_fullfiled: int


class AuctionOutput(NamedTuple):
    bid_outputs: Iterable[BidOutput]
    sorted_bids: Iterable[Bid]


Operation = IntEnum("Operation", ["TRANSFER", "MINT", "BURN"])


class Voucher(NamedTuple):
    op: Operation
    user: Address
    amount: int
    timestamp_locked: bool


def auction_output(bids: Iterable[Bid], volume_limit: int) -> AuctionOutput:
    sorted_bids = sorted(bids, key=lambda bid: bid.price, reverse=True)
    accumulated_budget = accumulate(
        sorted_bids, lambda acc, bid: acc - bid.volume, initial=volume_limit
    )  # each bid consumes the auction amount limit.

    def fullfiled_volume(bid, budget):
        return BidOutput(bid.bidder, bid.volume, max(min(budget, bid.volume), 0))

    outputs = starmap(fullfiled_volume, zip(sorted_bids, accumulated_budget))
    return AuctionOutput(outputs, sorted_bids)


def auction_price(output: AuctionOutput) -> int:
    sorted_bids = output.sorted_bids
    outputs = output.bid_outputs
    bid, _ = min(
        filter(lambda x: x[1].amount_fullfiled > 0, zip(sorted_bids, outputs)),
        key=lambda x: x[0].price,
    )
    return bid.price


def generate_bid_vouchers(output: BidOutput, price: int) -> Iterable[Voucher]:
    decimal_price = price / PRICE_DECIMALS
    not_fullfiled = int(output.amount_sent - output.amount_fullfiled)
    mint_amount = int(
        max((1 - decimal_price) * output.amount_fullfiled // decimal_price, 0)
    )
    burn_amount = int(
        max((decimal_price - 1) * output.amount_fullfiled // decimal_price, 0)
    )
    return_voucher = Voucher(
        Operation.TRANSFER,
        output.bidder,
        not_fullfiled,
        timestamp_locked=False,
    )
    bid_portion_voucher = Voucher(
        Operation.TRANSFER,
        user=output.bidder,
        amount=output.amount_fullfiled - burn_amount,
        timestamp_locked=True,
    )
    mint_voucher = Voucher(
        Operation.MINT,
        user=output.bidder,
        amount=mint_amount,
        timestamp_locked=True,
    )
    burn_voucher = Voucher(
        Operation.BURN,
        user=output.bidder,
        amount=burn_amount,
        timestamp_locked=True,
    )
    return filter(
        lambda voucher: voucher.amount > 0,
        [return_voucher, bid_portion_voucher, mint_voucher, burn_voucher],
    )


def auction_vouchers(outputs: Iterable[BidOutput], price: int) -> Iterable[Voucher]:
    return chain(map(lambda output: generate_bid_vouchers(output, price), outputs))


def aggregate_vouchers(vouchers: Iterable[Voucher]) -> Iterable[Voucher]:
    voucher_key = lambda voucher: (
        voucher.op,
        voucher.user,
        voucher.timestamp_locked,
    )
    sorted_vouchers = sorted(vouchers, key=voucher_key)
    grouped_vouchers = groupby(sorted_vouchers, key=voucher_key)
    return [
        Voucher(
            op=key[0],
            user=key[1],
            timestamp_locked=key[2],
            amount=sum((voucher.amount for voucher in group)),
        )
        for key, group in grouped_vouchers
    ]
