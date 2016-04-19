from aspyrobotmx import RobotClientMX
from mock import MagicMock, call
import pytest


@pytest.fixture
def client():
    client = RobotClientMX()
    client.run_operation = MagicMock()
    return client


def test_probe(client):
    ports = {'left': [1, 0]}
    client.probe(ports)
    assert client.run_operation.call_args == call('probe', ports=ports)


def test_calibrate(client):
    client.calibrate('toolset', '1 0')
    assert client.run_operation.call_args == call('calibrate', target='toolset',
                                                  run_args='1 0')


def test_set_gripper(client):
    client.set_gripper(1)
    assert client.run_operation.call_args == call('set_gripper', value=1)


def test_set_lid(client):
    client.set_lid(1)
    assert client.run_operation.call_args == call('set_lid', value=1)


def test_set_port_state(client):
    position = 'left'
    column = 'A'
    port = 1
    state = 2
    client.set_port_state(position, column, port, state)
    assert client.run_operation.call_args == call(
        'set_port_state', position=position, column=column, port=port, state=state
    )


def test_set_holder_type(client):
    client.set_holder_type('left', 0)
    assert client.run_operation.call_args == call('set_holder_type',
                                                  position='left', type=0)