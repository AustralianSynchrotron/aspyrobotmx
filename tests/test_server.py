from unittest.mock import create_autospec

import pytest
import epics

import aspyrobotmx
from aspyrobotmx import RobotServerMX, RobotMX
from aspyrobotmx.codes import SampleState


aspyrobotmx.DELAY_TO_PROCESS = .01

UPDATE_ADDR = 'tcp://127.0.0.1:3000'
REQUEST_ADDR = 'tcp://127.0.0.1:3001'

HANDLE = 1


def process():
    epics.poll(.01)


@pytest.yield_fixture
def server():
    make_safe = create_autospec('aspyrobotmx.make_safe.MakeSafe')
    server = RobotServerMX(robot=RobotMX('ROBOT_MX_TEST:'),
                           update_addr=UPDATE_ADDR,
                           request_addr=REQUEST_ADDR,
                           make_safe=make_safe)
    server.robot.task_args.put(b'\0')
    server.robot.generic_command.put(b'\0')
    server.robot.left_probe_request.put(b'\0')
    server.robot.middle_probe_request.put(b'\0')
    server.robot.right_probe_request.put(b'\0')
    server.robot.heater_command.put(0)
    server.robot.heater_air_command.put(0)
    process()
    yield server


def operation_updates(server):
    while True:
        message = server.publish_queue.get(timeout=1.)
        if message['type'] != 'operation':
            continue
        yield message
        if message['stage'] == 'end':
            break


def test_refresh_yields_strings_for_char_arrays(server):
    update = server.refresh()
    assert isinstance(update['data']['task_message'], str)


def test_probe(server):
    ports = {'left': [0] * 96, 'middle': [0] * 96, 'right': [1] * 96}
    server.probe(HANDLE, ports)
    assert server.robot.left_probe_request.char_value == '0' * 96
    assert server.robot.middle_probe_request.char_value == '0' * 96
    assert server.robot.right_probe_request.char_value == '1' * 96
    assert server.robot.generic_command.char_value == 'ProbeCassettes'


def test_probe_when_busy(server):
    server._foreground_lock.acquire()
    ports = {'left': [0] * 96, 'middle': [0] * 96, 'right': [1] * 96}
    server.probe(HANDLE, ports)
    end_update = list(operation_updates(server))[-1]
    assert 'busy' in end_update['error']


def test_calibrate_invalid_target(server):
    server.calibrate(HANDLE, 'blah', '1 0')
    end_update = list(operation_updates(server))[-1]
    assert end_update['error'] is not None


def test_calibrate_toolset(server):
    server.calibrate(HANDLE, 'toolset', '1 0')
    assert server.robot.task_args.char_value == '1 0'


def test_calibrate_when_busy(server):
    server._foreground_lock.acquire()
    server.calibrate(HANDLE, 'toolset', '1 0')
    end_update = list(operation_updates(server))[-1]
    assert end_update['error'] is not None


def test_fetch_all_data(server):
    server.fetch_all_data()
    process()
    assert server.robot.task_args.char_value == 'PSDC LMR'
    assert server.robot.generic_command.char_value == 'DataRequest'


def test_set_port_state_can_set_single_ports_to_error(server):
    server.set_port_state(HANDLE, 'left', 'A', 1, 2)
    process()
    assert server.robot.task_args.char_value == 'L A 1 2'
    assert server.robot.generic_command.char_value == 'SetPortState'


def test_reset_ports(server):
    ports = {'left': [0] * 96, 'middle': [0] * 96, 'right': [1] * 96}
    server.reset_ports(HANDLE, ports)
    process()
    assert server.robot.left_probe_request.char_value == '0' * 96
    assert server.robot.middle_probe_request.char_value == '0' * 96
    assert server.robot.right_probe_request.char_value == '1' * 96
    assert server.robot.generic_command.char_value == 'ResetCassettePorts'


def test_set_heater(server):
    server.set_heater(HANDLE, 1)
    process()
    assert server.robot.heater_command.value == 1


def test_set_heater_air(server):
    server.set_heater_air(HANDLE, 1)
    process()
    assert server.robot.heater_air_command.value == 1


def test_reset_holders(server):
    server.reset_holders(HANDLE, ['left', 'right'])
    process()
    assert server.robot.task_args.char_value == 'LR'
    assert server.robot.generic_command.char_value == 'ResetCassettes'


def test_set_sample_state(server):
    server.set_sample_state(HANDLE, 'left', 'A', 1, SampleState.goniometer)
    process()
    assert server.robot.task_args.char_value == 'LA1 goniometer'
    assert server.robot.generic_command.char_value == 'SetSampleStatus'
