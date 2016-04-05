from threading import Thread
from types import MethodType
import time

import pytest
from mock import MagicMock
import epics

from aspyrobotmx import RobotClientMX, RobotServerMX
from aspyrobot.server import foreground_operation, query_operation


handle = 1


@pytest.yield_fixture
def server():
    robot = MagicMock()
    robot.snapshot.return_value = {}
    server = RobotServerMX(robot=robot, logger=MagicMock())
    server.setup()
    yield server
    server.shutdown()
    time.sleep(.05)


@pytest.fixture
def client():
    client = RobotClientMX()
    client.setup()
    return client


def test_operation_works(server, client):
    response = client.set_lid(1)
    assert response['error'] is None


def test_query_operation(server, client):
    response = client.run_operation('refresh')
    assert response['error'] is None
