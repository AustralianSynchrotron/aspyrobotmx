from aspyrobotmx import RobotServerMX, RobotMX
import pytest
import epics


@pytest.fixture
def server():
    server = RobotServerMX(RobotMX('ROBOT_MX_TEST:'))
    server.robot.put('run_args', b'\0')
    server.robot.put('generic_command', b'\0')
    epics.poll(.01)
    return server


def test_refresh_yields_strings_for_char_arrays(server):
    state = server.refresh()
    assert isinstance(state['task_message'], str)


def test_probe(server):
    ports = {'left': [0] * 96, 'middle': [0] * 96, 'right': [1] * 96}
    result = server.probe(ports)
    assert result.get('error') is None
    assert server.robot.PV('left_probe_request').char_value == '0' * 96
    assert server.robot.PV('middle_probe_request').char_value == '0' * 96
    assert server.robot.PV('right_probe_request').char_value == '1' * 96
    assert server.robot.PV('generic_command').char_value == 'ProbeCassettes'


def test_probe_when_busy(server):
    server.foreground_operation_lock.acquire()
    ports = {'left': [0] * 96, 'middle': [0] * 96, 'right': [1] * 96}
    result = server.probe(ports)
    assert result['error'] == 'busy'


def test_calibrate_invalid_target(server):
    result = server.calibrate('blah', '1 0')
    assert result['error'] is not None


def test_calibrate_toolset(server):
    result = server.calibrate('toolset', '1 0')
    assert result.get('error') is None
    assert server.robot.PV('run_args').char_value == '1 0'


def test_calibrate_when_busy(server):
    server.foreground_operation_lock.acquire()
    result = server.calibrate('toolset', '1 0')
    assert result['error'] == 'busy'


def test_fetch_all_data(server):
    server.fetch_all_data()
    epics.poll(.1)
    assert server.robot.PV('run_args').char_value == 'PSDC LMR'
    assert server.robot.PV('generic_command').char_value == 'JSONDataRequest'


def test_clear(server):
    server.clear()
    epics.poll(.1)
    # TODO: Still needs to be implemented in SPEL
    assert server.robot.PV('generic_command').char_value == 'ClearSamplePositions'
