import unittest

from auction import *


class BidsTest(unittest.TestCase):
    def setUp(self):
        self.auction = Auction(200, 100, 100, 5000, [])
        self.b1 = Bid(95, 100, 5500, Address("alice"))
        self.b2 = Bid(95, 100, 2000, Address("bob"))
        self.b3 = Bid(1100, 110, 7000, Address("charles"))
        self.b4 = Bid(95, 100, 7100, Address("evan"))
        self.b5 = Bid(95, 90, 8000, Address("felicia"))

        self.bid_list = [self.b1, self.b2, self.b3, self.b4, self.b5]

    def add_bids(self):
        expected_filtered_bids = [self.b1, self.b5]
        for bid in self.bid_list:
            try:
                self.auction.new_bid(bid)
            except:
                continue
        self.assertEqual(
            self.auction.bids, expected_filtered_bids, "wrong list of filtered bids"
        )

    def test_auction_output(self):
        VOLUME_LIMIT = 250
        bid_output1 = BidOutput(self.b1.bidder, self.b1.volume, 0)
        bid_output2 = BidOutput(self.b2.bidder, self.b2.volume, 0)
        bid_output3 = BidOutput(self.b3.bidder, self.b3.volume, 60)
        bid_output4 = BidOutput(self.b4.bidder, self.b4.volume, 100)
        bid_output5 = BidOutput(self.b5.bidder, self.b5.volume, 90)
        expected_outputs = [
            bid_output5,
            bid_output4,
            bid_output3,
            bid_output1,
            bid_output2,
        ]
        bids_outputs = list(auction_output(self.bid_list, VOLUME_LIMIT).bid_outputs)
        self.assertEqual(bids_outputs, expected_outputs, "wrong list of outputs bids")
        sum_of_fullfill = sum([output.amount_fullfiled for output in bids_outputs])
        self.assertEqual(sum_of_fullfill, VOLUME_LIMIT)

    def test_auction_price(self):
        VOLUME_LIMIT = 250
        auction_outputs = auction_output(self.bid_list, VOLUME_LIMIT)
        price = auction_price(auction_outputs)
        self.assertEqual(price, 7000)

    def test_generate_bid_vouchers_no_fullfiled(self):
        price = int(0.7*PRICE_DECIMALS)
        output = BidOutput(Address("alice"), 100, 0)
        expected = [
            Voucher(
                Operation.TRANSFER,
                Address("alice"),
                100,
                False,
            )
        ]
        self.assertEqual(list(generate_bid_vouchers(output, price)), expected)

    def test_generate_bid_vouchers_mint(self):
        price = int(0.7*PRICE_DECIMALS)
        output = BidOutput(Address("alice"), 100, 70)
        expected = [
            Voucher(
                Operation.TRANSFER,
                Address("alice"),
                30,
                False,
            ),
            Voucher(
                Operation.TRANSFER,
                Address("alice"),
                70,
                True,
            ),
            Voucher(
                Operation.MINT, Address("alice"), 30, True
            ),
        ]
        self.assertEqual(set(generate_bid_vouchers(output, price)), set(expected))

    def test_generate_bid_vouchers_burn(self):
        price = int(1.1*PRICE_DECIMALS)
        output = BidOutput(Address("alice"), 100, 80)
        expected = [
            Voucher(
                Operation.TRANSFER,
                Address("alice"),
                20,
                False,
            ),
            Voucher(
                Operation.TRANSFER,
                Address("alice"),
                73,
                True,
            ),
            Voucher(
                Operation.BURN,
                Address("alice"),
                int(7),
                True,
            ),
        ]
        self.assertEqual(list(generate_bid_vouchers(output, price)), expected)

    def test_aggregate_vouchers(self):
        vouchers = [
            Voucher(
                Operation.BURN,
                Address("alice"),
                int(57),
                True,
            ),
            Voucher(
                Operation.TRANSFER,
                Address("alice"),
                20,
                False,
            ),
            Voucher(
                Operation.TRANSFER,
                Address("alice"),
                73,
                True,
            ),
            Voucher(
                Operation.BURN,
                Address("alice"),
                int(7),
                True,
            ),
        ]
        aggregated_vouchers = set(aggregate_vouchers(vouchers))
        expected = set(
            [
                Voucher(
                    Operation.BURN,
                    Address("alice"),
                    int(64),
                    True,
                ),
                Voucher(
                    Operation.TRANSFER,
                    Address("alice"),
                    20,
                    False,
                ),
                Voucher(
                    Operation.TRANSFER,
                    Address("alice"),
                    73,
                    True,
                ),
            ]
        )
        self.assertEqual(aggregated_vouchers, expected)


if __name__ == "__main__":
    unittest.main()
