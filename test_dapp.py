import pytest
from auction import Auction

from cartesi.testclient import TestClient

import dapp


@pytest.fixture
def dapp_client() -> TestClient:
    client = TestClient(dapp.dapp)
    return client


def test_simple_set_get(dapp_client: TestClient):

    set_payload = dapp.to_jsonhex(
         {'op': 'new-auction', 'id': 'key_1', 'end_time': 100, 'lock_time': 200, 'reserve_price': 7000, 'volume_limit':2000}
    )
    dapp_client.send_advance(hex_payload=set_payload)

    assert dapp_client.rollup.status
    assert len(dapp_client.rollup.notices) == 0

    get_payload = dapp.to_jsonhex(
        {'op': 'get', 'id': 'key_1'}
    )
    dapp_client.send_advance(hex_payload=get_payload)
    assert dapp_client.rollup.status
    expected_payload =dapp.to_jsonhex(
        {'key_1': (100, 200, 7000, 2000, [])}
    )
    
    #assert dapp_client.rollup.reports[-1]['data']['payload'] == expected_payload

