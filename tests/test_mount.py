import pytest
import epics

from aspyrobotmx import RobotServerMX
from aspyrobotmx import RobotMX


UPDATE_ADDR = 'tcp://127.0.0.1:3000'
REQUEST_ADDR = 'tcp://127.0.0.1:3001'

handle = 1


def process():
    epics.poll(.01)


@pytest.yield_fixture
def server():
    server = RobotServerMX(robot=RobotMX('ROBOT_MX_TEST:'),
                           update_addr=UPDATE_ADDR,
                           request_addr=REQUEST_ADDR)
    server.robot.closest_point.put(0)
    server.robot.run_args.put(b'\0')
    server.robot.generic_command.put(b'\0')
    process()
    yield server


def test_mount_sends_the_mount_command(server):
    server.robot.closest_point.put(3)
    process()
    server.mount(handle, 'left', 'A', '1')
    process()
    assert server.robot.run_args.char_value == 'L A 1'
    assert server.robot.generic_command.char_value == 'MountSamplePortAndGoHome'


def test_dismount_sends_the_dismount_command(server):
    server.robot.closest_point.put(3)
    process()
    server.dismount(handle, 'left', 'A', '1')
    process()
    assert server.robot.run_args.char_value == 'L A 1'
    assert server.robot.generic_command.char_value == 'DismountSample'
