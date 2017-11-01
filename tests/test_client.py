from unittest.mock import MagicMock, call

import pytest

from aspyrobotmx import RobotClientMX
from aspyrobotmx.server import Position


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
    assert client.run_operation.call_args == call('probe', ports=ports,
                                                  callback=None)


def test_set_gripper(client):
    client.set_gripper(1)
    assert client.run_operation.call_args == call('set_gripper', value=1,
                                                  callback=None)


def test_set_lid(client):
    client.set_lid(1)
    assert client.run_operation.call_args == call('set_lid', value=1, callback=None)


def test_set_heater(client):
    client.set_heater(1)
    assert client.run_operation.call_args == call('set_heater',
                                                  value=1, callback=None)


def test_set_heater_air(client):
    client.set_heater_air(1)
    assert client.run_operation.call_args == call('set_heater_air',
                                                  value=1, callback=None)


def test_reset_holders(client):
    client.reset_holders(['left', 'right'])
    assert client.run_operation.call_args == call('reset_holders',
                                                  positions=['left', 'right'],
                                                  callback=None)


def test_calibrate_toolset(client):
    client.calibrate_toolset(include_find_magnet=True, quick_mode=False)
    assert client.run_operation.call_args == call('calibrate_toolset',
                                                  include_find_magnet=True,
                                                  quick_mode=False,
                                                  callback=None)


def test_calibrate_cassettes(client):
    client.calibrate_cassettes([Position.LEFT], False)
    assert client.run_operation.call_args == call('calibrate_cassettes',
                                                  positions=['left'], initial=False,
                                                  callback=None)


def test_calibrate_goniometer(client):
    client.calibrate_goniometer(False)
    assert client.run_operation.call_args == call('calibrate_goniometer',
                                                  initial=False, callback=None)
