from unittest.mock import create_autospec, call, Mock

import pytest

import epics

import aspyrobotmx
from aspyrobotmx import RobotServerMX
from aspyrobotmx.server import Port
from aspyrobotmx.make_safe import MakeSafe, MakeSafeFailed
from aspyrobot.exceptions import RobotError


aspyrobotmx.DELAY_TO_PROCESS = .01

UPDATE_ADDR = 'tcp://127.0.0.1:3000'
REQUEST_ADDR = 'tcp://127.0.0.1:3001'

HANDLE = 101


@pytest.fixture
def make_safe():
    yield create_autospec(MakeSafe, instance=True)


@pytest.fixture
def robot():
    robot = create_autospec(aspyrobotmx.RobotMX)
    robot.configure_mock(foreground_done=Mock(value=True))
    robot.configure_mock(goniometer_sample=create_autospec(epics.PV))
    yield robot


@pytest.fixture
def server(robot, make_safe):
    server = RobotServerMX(robot=robot, make_safe=make_safe,
                           update_addr=UPDATE_ADDR, request_addr=REQUEST_ADDR)
    yield server


def _get_all_updates(server):
    while True:
        update = server.publish_queue.get_nowait()
        yield update
        if update['stage'] == 'end':
            break


def _get_end_update(server):
    return list(_get_all_updates(server))[-1]


def process():
    epics.poll(.5)


def test_mount(server, robot, make_safe):
    server.mount(HANDLE, 'left', 'A', 1)
    assert robot.prepare_for_mount.called is True
    assert make_safe.move_to_safe_position.called is True
    assert robot.mount.call_args == call(Port('left', 'A', 1))
    assert robot.return_placer.called is True
    assert make_safe.return_positions.called is True
    assert robot.go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] is None


def test_dismount_uses_mounted_port(server, robot, make_safe):
    server.robot.goniometer_sample.get.return_value = 'L A 1'
    server.dismount(HANDLE)
    assert robot.prepare_for_mount.called is True
    assert make_safe.move_to_safe_position.called is True
    assert robot.dismount.call_args == call(Port('left', 'A', 1))
    assert make_safe.return_positions.called is True
    assert robot.go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] is None


def test_dismount_does_nothing_if_no_sample_on_goni(server, robot, make_safe):
    server.robot.goniometer_sample.get.return_value = ''
    server.dismount(HANDLE)
    assert robot.prepare_for_mount.called is False
    assert make_safe.move_to_safe_position.called is False
    update = _get_end_update(server)
    assert update['error'] is None
    assert update['message'] == 'no sample mounted'


def test_mount_and_prefetch_calls_prepare(server, robot, make_safe):
    server.mount_and_prefetch(HANDLE, 'left', 'A', 1, 'right', 'B', 2)
    assert robot.prepare_for_mount.called is True
    assert make_safe.move_to_safe_position.called is True
    assert robot.mount.call_args == call(Port('left', 'A', 1))
    assert robot.return_placer.called is True
    assert make_safe.return_positions.called is True
    assert robot.prefetch.call_args == call(Port('right', 'B', 2))
    assert robot.go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] is None


def test_mount_and_prefetch_calls_standby_if_make_safe_fails(server, robot, make_safe):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.mount_and_prefetch(HANDLE, 'left', 'A', 1, 'right', 'B', 2)
    assert robot.mount.called is False
    assert robot.go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] == 'make safe failed: bad bad happened'


def test_mount_and_prefetch_doesnt_call_standby_if_prepare_fails(
        server, robot, make_safe):
    robot.prepare_for_mount.side_effect = RobotError()
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed()
    server.mount_and_prefetch(HANDLE, 'left', 'A', 1, 'right', 'B', 2)
    assert robot.mount.called is False
    assert robot.go_to_standby.called is False
    update = _get_end_update(server)
    assert update['error'] is not None


def test_mount_and_prefetch_goes_to_standby_if_make_safe_return_fails(
        server, robot, make_safe):
    make_safe.return_positions.side_effect = MakeSafeFailed('bad bad happened')
    server.mount_and_prefetch(HANDLE, 'left', 'A', 1, 'right', 'B', 2)
    assert make_safe.return_positions.called is True
    assert robot.prefetch.call_args == call(Port('right', 'B', 2))
    assert robot.go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] == 'undo make safe failed: bad bad happened'


def test_mount_and_prefetch_prioritises_robot_error_over_makesafe(
        server, robot, make_safe):
    make_safe.return_positions.side_effect = MakeSafeFailed('make safe error')
    robot.return_placer.side_effect = RobotError('robot error')
    server.mount_and_prefetch(HANDLE, 'left', 'A', 1, 'right', 'B', 2)
    assert make_safe.return_positions.called is True
    assert robot.prefetch.called is False
    assert robot.go_to_standby.called is False
    updates = list(_get_all_updates(server))
    make_safe_update = updates[-2]
    assert make_safe_update['stage'] == 'update'
    assert make_safe_update['error'] == 'make safe error'
    assert updates[-1]['error'] == 'robot error'


def test_prefetch(server, robot):
    server.prefetch(HANDLE, 'left', 'A', 1)
    assert robot.prepare_for_mount.called is True
    assert robot.prefetch.call_args == call(Port('left', 'A', 1))
    assert robot.go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] is None


def test_return_prefetch(server, robot):
    server.return_prefetch(HANDLE)
    assert robot.prepare_for_mount.called is True
    assert robot.return_prefetch.call_args == call()
    assert robot.go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] is None
