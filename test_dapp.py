import pytest
from cartesi.testclient import TestClient

import dapp
from auction import Auction


@pytest.fixture
def dapp_client() -> TestClient:
    client = TestClient(dapp.dapp)
    return client


def test_simple_set_get(dapp_client: TestClient):

    set_payload = dapp.to_jsonhex(
        {
            "op": "new-auction",
            "end_time": 100,
            "lock_time": 200,
            "reserve_price": 7000,
            "volume_limit": 2000,
        }
    )
    dapp_client.send_advance(hex_payload=set_payload)

    assert dapp_client.rollup.status
    assert len(dapp_client.rollup.notices) == 0

    get_payload = dapp.to_jsonhex({"op": "get", "key": "0"})
    # dapp_client.send_advance(hex_payload=get_payload)
    expected_payload = dapp.state2hex([Auction(100, 200, 7000, 2000, [])])
    assert dapp_client.rollup.status

    # assert dapp_client.rollup.reports[-1]['data']['payload'] == expected_payload
