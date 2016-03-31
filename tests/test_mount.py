from aspyrobotmx import RobotServerMX
from aspyrobotmx import RobotMX
import pytest
import epics


def process():
    epics.poll(.01)


@pytest.fixture
def server():
    server = RobotServerMX(RobotMX('ROBOT_MX_TEST:'))
    server.robot.put('closest_point', 0)
    server.robot.put('run_args', b'\0')
    server.robot.put('generic_command', b'\0')
    process()
    return server


def test_prepare_for_mount_sends_robot_to_cooling_point(server):
    result = server.prepare_for_mount()
    process()
    assert result is None
    assert server.robot.PV('generic_command').char_value == 'PrepareForMountDismount'


def test_prepare_for_mount_fails_if_not_at_home(server):
    server.robot.put('closest_point', 22)
    process()
    result = server.prepare_for_mount()
    assert result['error'] is not None


def test_mount_sends_the_mount_command(server):
    server.robot.put('closest_point', 3)
    process()
    server.mount('left', 'A', '1')
    process()
    assert server.robot.PV('run_args').char_value == 'L A 1'
    assert server.robot.PV('generic_command').char_value == 'MountSamplePort'


def test_mount_fails_if_not_at_cooling_point(server):
    server.robot.put('closest_point', 22)
    process()
    result = server.mount('left', 'A', '1')
    assert result['error'] is not None


def test_dismount_sends_the_dismount_command(server):
    server.robot.put('closest_point', 3)
    process()
    server.dismount('left', 'A', '1')
    process()
    assert server.robot.PV('run_args').char_value == 'L A 1'
    assert server.robot.PV('generic_command').char_value == 'DismountSample'


def test_dismount_fails_if_not_at_cooling_point(server):
    server.robot.put('closest_point', 22)
    process()
    result = server.dismount('left', 'A', '1')
    assert result['error'] is not None
