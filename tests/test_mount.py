from unittest.mock import MagicMock, call
from time import sleep

import pytest
import epics

from aspyrobotmx import RobotServerMX
from aspyrobotmx import RobotMX


UPDATE_ADDR = 'tcp://127.0.0.1:3000'
REQUEST_ADDR = 'tcp://127.0.0.1:3001'

HANDLE = 1


def process():
    epics.poll(.01)


@pytest.yield_fixture
def server():
    server = RobotServerMX(robot=RobotMX('ROBOT_MX_TEST:'),
                           update_addr=UPDATE_ADDR,
                           request_addr=REQUEST_ADDR)
    server.robot.closest_point.put(0)
    server.robot.task_args.put(b'\0')
    server.robot.generic_command.put(b'\0')
    process()
    yield server


def test_mount_sends_the_mount_command(server):
    server._prepared_for_mount = True
    server.mount(HANDLE, 'left', 'A', '1')
    process()
    assert server.robot.task_args.char_value == 'L A 1'
    assert server.robot.generic_command.char_value == 'MountSamplePort'


def test_dismount_sends_the_dismount_command(server):
    server._prepared_for_mount = True
    server.dismount(HANDLE, 'left', 'A', '1')
    process()
    assert server.robot.task_args.char_value == 'L A 1'
    assert server.robot.generic_command.char_value == 'DismountSample'


def test_prepare_for_mount_starts_timeout_thread(server):
    server._start_prepare_timeout = MagicMock()
    server.robot.run_task = MagicMock(return_value='ok')
    server.prepare_for_mount(HANDLE)
    assert server._start_prepare_timeout.called is True


def test_start_prepare_timeout_should_reset_timeout_and_launch_thread(server):
    server._abort_prepare_timeout.set()
    server._prepare_timeout = MagicMock()
    server._start_prepare_timeout(120)
    sleep(.01)
    assert server._abort_prepare_timeout.is_set() is False
    assert server._prepare_timeout.call_args == call(120)


def test_prepare_timeout_should_start_error_task_if_timeout_runs_out(server):
    server.robot.run_task = MagicMock(return_value='ok')
    server._start_prepare_timeout(1)
    sleep(1.1)
    assert server.robot.run_task.call_args == call('GoHomeDueToError')


def test_prepare_timeout_should_cancel_if_abort_event_is_set(server):
    server.robot.run_task = MagicMock(return_value='ok')
    server._start_prepare_timeout(1)
    server._abort_prepare_timeout.set()
    sleep(1.1)
    assert server.robot.run_task.called is False
