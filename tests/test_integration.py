import time

import pytest
from mock import MagicMock

from aspyrobotmx import RobotClientMX, RobotServerMX


UPDATE_ADDR = 'tcp://127.0.0.1:3000'
REQUEST_ADDR = 'tcp://127.0.0.1:3001'

handle = 1


@pytest.yield_fixture
def server():
    robot = MagicMock()
    robot.snapshot.return_value = {}
    server = RobotServerMX(robot=robot, logger=MagicMock(),
                           update_addr=UPDATE_ADDR,
                           request_addr=REQUEST_ADDR)
    server.setup()
    yield server
    server.shutdown()
    time.sleep(.05)


@pytest.fixture
def client():
    client = RobotClientMX(update_addr=UPDATE_ADDR, request_addr=REQUEST_ADDR)
    client.setup()
    return client


def test_operation_works(server, client):
    response = client.set_lid(1)
    assert response['error'] is None


def test_query_operation(server, client):
    response = client.run_operation('refresh')
    assert response['error'] is None
