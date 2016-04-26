from aspyrobotmx import RobotClientMX
from mock import MagicMock, call
import pytest


UPDATE_ADDR = 'tcp://127.0.0.1:3000'
REQUEST_ADDR = 'tcp://127.0.0.1:3001'


@pytest.fixture
def client():
    client = RobotClientMX(update_addr=UPDATE_ADDR, request_addr=REQUEST_ADDR)
    client.run_operation = MagicMock()
    return client


def test_probe(client):
    ports = {'left': [1, 0]}
    client.probe(ports)
    assert client.run_operation.call_args == call('probe', ports=ports, callback=None)


def test_calibrate(client):
    client.calibrate('toolset', '1 0')
    assert client.run_operation.call_args == call('calibrate', target='toolset',
                                                  run_args='1 0', callback=None)


def test_set_gripper(client):
    client.set_gripper(1)
    assert client.run_operation.call_args == call('set_gripper', value=1, callback=None)


def test_set_lid(client):
    client.set_lid(1)
    assert client.run_operation.call_args == call('set_lid', value=1, callback=None)


def test_set_holder_type(client):
    client.set_holder_type('left', 0)
    assert client.run_operation.call_args == call('set_holder_type',
                                                  position='left', type=0,
                                                  callback=None)
