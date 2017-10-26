from unittest.mock import create_autospec

import pytest
import epics

import aspyrobotmx
from aspyrobotmx import RobotServerMX, RobotMX
from aspyrobotmx.server import Port
from aspyrobot.exceptions import RobotError


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
    server.robot.closest_point.put(0)
    server.robot.task_args.put(b'\0')
    server.robot.generic_command.put(b'\0')
    process()
    yield server


def test_mount_sends_the_mount_command(server):
    try:
        server._mount(HANDLE, Port('left', 'A', '1'))
    except RobotError:
        pass
    process()
    assert server.robot.task_args.char_value == 'L A 1'
    assert server.robot.generic_command.char_value == 'MountSamplePort'


def test_dismount_sends_the_dismount_command(server):
    try:
        server._dismount(HANDLE, Port('left', 'A', '1'))
    except RobotError:
        pass
    process()
    assert server.robot.task_args.char_value == 'L A 1'
    assert server.robot.generic_command.char_value == 'DismountSample'
