import pytest
import epics

from aspyrobotmx import RobotMX
from aspyrobotmx.server import Port, Position
from aspyrobot.exceptions import RobotError


def process():
    epics.poll(.01)


@pytest.fixture
def robot():
    robot = RobotMX('ROBOT_MX_TEST:')
    robot.task_args.put(b'\0')
    robot.generic_command.put(b'\0')
    process()
    yield robot


def test_mount_sends_the_mount_command(robot):
    try:
        robot.mount(Port('left', 'A', '1'))
    except RobotError:
        pass
    process()
    assert robot.task_args.char_value == 'L A 1'
    assert robot.generic_command.char_value == 'MountSamplePort'


def test_dismount_sends_the_dismount_command(robot):
    try:
        robot.dismount(Port('right', 'B', '2'))
    except RobotError:
        pass
    process()
    assert robot.task_args.char_value == 'R B 2'
    assert robot.generic_command.char_value == 'DismountSample'


def test_calibrate_toolset(robot):
    try:
        robot.calibrate_toolset(include_find_magnet=True, quick_mode=False)
    except RobotError:
        pass
    process()
    assert robot.task_args.char_value == '1 0'
    assert robot.generic_command.char_value == 'VB_MagnetCal'


def test_calibrate_casettes(robot):
    try:
        robot.calibrate_cassettes(positions=[Position.LEFT, Position.RIGHT],
                                  initial=False)
    except RobotError:
        pass
    process()
    assert robot.task_args.char_value == 'lr 0'
    assert robot.generic_command.char_value == 'VB_CassetteCal'


def test_calibrate_goniometer(robot):
    try:
        robot.calibrate_goniometer(initial=True)
    except RobotError:
        pass
    process()
    assert robot.task_args.char_value == '1 0 0 0 0'
    assert robot.generic_command.char_value == 'VB_GonioCal'
