from unittest.mock import create_autospec, call, ANY

import pytest

import aspyrobotmx
from aspyrobotmx import RobotServerMX, RobotMX
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
def server(make_safe):
    server = RobotServerMX(robot=RobotMX('ROBOT_MX_TEST:'),
                           make_safe=make_safe,
                           update_addr=UPDATE_ADDR,
                           request_addr=REQUEST_ADDR)
    yield server


@pytest.fixture
def prepare_for_mount(mocker, server):
    yield mocker.patch.object(server, '_prepare_for_mount', autospec=True)


@pytest.fixture
def mount(mocker, server):
    yield mocker.patch.object(server, '_mount', autospec=True)


@pytest.fixture
def return_placer(mocker, server):
    yield mocker.patch.object(server, '_return_placer', autospec=True)


@pytest.fixture
def prefetch(mocker, server):
    yield mocker.patch.object(server, '_prefetch', autospec=True)


@pytest.fixture
def go_to_standby(mocker, server):
    yield mocker.patch.object(server, '_go_to_standby', autospec=True)


def _get_all_updates(server):
    while True:
        update = server.publish_queue.get_nowait()
        yield update
        if update['stage'] == 'end':
            break


def _get_end_update(server):
    return list(_get_all_updates(server))[-1]


def test_mount_and_premount_calls_prepare(
        server, prepare_for_mount, mount, return_placer, prefetch, go_to_standby,
        make_safe):
    server.mount_and_premount(HANDLE, 'left', 'A', '1', 'right', 'B', '2')
    assert prepare_for_mount.called is True
    assert make_safe.move_to_safe_position.called is True
    assert mount.call_args == call(ANY, 'left', 'A', '1')
    assert return_placer.called is True
    assert make_safe.return_positions.called is True
    assert prefetch.call_args == call(ANY, 'right', 'B', '2')
    assert go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] is None


def test_mount_and_premount_calls_go_to_standby_if_make_safe_fails(
        server, prepare_for_mount, mount, return_placer, prefetch, go_to_standby,
        make_safe):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.mount_and_premount(HANDLE, 'left', 'A', '1', 'right', 'B', '2')
    assert mount.called is False
    assert go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] == 'make safe failed: bad bad happened'


def test_mount_and_premount_doesnt_call_go_to_standby_if_prepare_fails(
        server, prepare_for_mount, mount, return_placer, prefetch, go_to_standby,
        make_safe):
    prepare_for_mount.side_effect = RobotError()
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed()
    server.mount_and_premount(HANDLE, 'left', 'A', '1', 'right', 'B', '2')
    assert mount.called is False
    assert go_to_standby.called is False
    update = _get_end_update(server)
    assert update['error'] is not None


def test_mount_and_premount_goes_to_standby_if_make_safe_return_fails(
        server, prepare_for_mount, mount, return_placer, prefetch, go_to_standby,
        make_safe):
    make_safe.return_positions.side_effect = MakeSafeFailed('bad bad happened')
    server.mount_and_premount(HANDLE, 'left', 'A', '1', 'right', 'B', '2')
    assert make_safe.return_positions.called is True
    assert prefetch.call_args == call(ANY, 'right', 'B', '2')
    assert go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] == 'undo make safe failed: bad bad happened'


def test_mount_and_premount_prioritises_robot_error_over_makesafe(
        server, prepare_for_mount, mount, return_placer, prefetch, go_to_standby,
        make_safe):
    make_safe.return_positions.side_effect = MakeSafeFailed('make safe error')
    return_placer.side_effect = RobotError('robot error')
    server.mount_and_premount(HANDLE, 'left', 'A', '1', 'right', 'B', '2')
    assert make_safe.return_positions.called is True
    assert prefetch.called is False
    assert go_to_standby.called is False
    updates = list(_get_all_updates(server))
    make_safe_update = updates[-2]
    assert make_safe_update['stage'] == 'update'
    assert make_safe_update['error'] == 'make safe error'
    assert updates[-1]['error'] == 'robot error'
