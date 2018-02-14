from unittest.mock import create_autospec, call, Mock
import threading
import time

import pytest

import epics

import aspyrobotmx
from aspyrobotmx import RobotServerMX
from aspyrobotmx.server import Port, Position
from aspyrobotmx.make_safe import MakeSafe, MakeSafeFailed
from aspyrobot.exceptions import RobotError


aspyrobotmx.DELAY_TO_PROCESS = .01

UPDATE_ADDR = 'tcp://127.0.0.1:13000'
REQUEST_ADDR = 'tcp://127.0.0.1:13001'

HANDLE = 101


@pytest.fixture
def make_safe():
    yield create_autospec(MakeSafe, instance=True)


@pytest.fixture
def robot():
    robot = create_autospec(aspyrobotmx.RobotMX)
    robot.configure_mock(foreground_done=Mock(value=True))
    robot.configure_mock(goniometer_sample=create_autospec(epics.PV))
    robot.configure_mock(goniometer_locked=create_autospec(epics.PV))
    yield robot


@pytest.fixture
def server(robot, make_safe):
    yield make_server(robot, make_safe)


def make_server(robot, make_safe):
    return RobotServerMX(robot=robot, make_safe=make_safe,
                         update_addr=UPDATE_ADDR, request_addr=REQUEST_ADDR)


def allow_threads_to_progress():
    time.sleep(.01)


def _get_all_updates(server):
    while True:
        update = server.publish_queue.get_nowait()
        yield update
        if update.get('stage') == 'end':
            break


def _get_end_update(server):
    return list(_get_all_updates(server))[-1]


def process():
    epics.poll(.5)


def test_mount(robot, make_safe, server, mocker):

    make_safe_complete = threading.Event()
    make_safe.move_to_safe_position.side_effect = lambda: make_safe_complete.wait()

    mount_complete = threading.Event()
    robot.mount.side_effect = lambda port: mount_complete.wait()

    mount_thread = threading.Thread(target=server.mount, args=(HANDLE, 'left', 'A', 1))
    mount_thread.start()

    # server first runs makesafe and prepares for mount
    allow_threads_to_progress()
    assert robot.goniometer_locked.put.call_args == call(True)
    assert robot.set_auto_heat_cool_allowed.call_args == call(False)
    assert make_safe.move_to_safe_position.called is True
    assert robot.prepare_for_mount.called is True
    assert robot.return_placer_and_prefetch.call_args == call(Port('left', 'A', 1))
    assert server.motors_locked is True
    robot.return_placer_and_prefetch.reset_mock()
    robot.set_auto_heat_cool_allowed.reset_mock()

    # until makesafe is complete, robot must not have received mount command
    assert robot.mount.called is False

    # once makesafe is complete we can proceed with mount
    make_safe_complete.set()
    allow_threads_to_progress()
    assert robot.mount.call_args == call(Port('left', 'A', 1))

    # before mount is complete we shouldn't have undone the makesafe
    assert robot.return_placer_and_prefetch.called is False
    assert make_safe.return_positions.called is False
    assert robot.go_to_standby.called is False
    assert server.motors_locked is True

    # once mount is complete, undo-makesafe and return placer can proceed
    mount_complete.set()
    mount_thread.join()

    assert robot.goniometer_locked.put.call_args == call(False)
    assert robot.return_placer_and_prefetch.call_args == call(None)
    assert make_safe.return_positions.called is True
    assert robot.go_to_standby.called is True
    assert server.motors_locked is False
    assert robot.set_auto_heat_cool_allowed.call_args == call(True)

    update = _get_end_update(server)
    assert update['error'] is None


def test_mount_enables_auto_heat_cool_allowed_if_makesafe_fails(server, make_safe, robot):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.mount(HANDLE, 'left', 'A', 1)
    assert robot.set_auto_heat_cool_allowed.call_args_list == [call(False), call(True)]


def test_mount_unlocks_motors_if_makesafe_fails(server, make_safe, robot):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.mount(HANDLE, 'left', 'A', 1)
    assert robot.goniometer_locked.put.call_args_list == [call(True), call(False)]


def test_dismount_uses_mounted_port(server, robot, make_safe):

    server.robot.goniometer_sample.get.return_value = 'L A 1'

    make_safe_complete = threading.Event()
    make_safe.move_to_safe_position.side_effect = lambda: make_safe_complete.wait()

    dismount_complete = threading.Event()
    robot.dismount.side_effect = lambda port: dismount_complete.wait()

    dismount_thread = threading.Thread(target=server.dismount, args=(HANDLE,))
    dismount_thread.start()
    allow_threads_to_progress()

    assert robot.set_auto_heat_cool_allowed.call_args == call(False)
    assert make_safe.move_to_safe_position.called is True
    assert robot.prepare_for_mount.called is True
    assert robot.return_placer_and_prefetch.call_args == call(None)
    assert server.motors_locked is True
    robot.return_placer_and_prefetch.reset_mock()
    robot.set_auto_heat_cool_allowed.reset_mock()

    make_safe_complete.set()
    allow_threads_to_progress()

    assert robot.dismount.call_args == call(Port('left', 'A', 1))
    assert robot.return_placer_and_prefetch.called is False
    assert robot.go_to_standby.called is False
    assert server.motors_locked is True

    dismount_complete.set()
    dismount_thread.join()

    assert make_safe.return_positions.called is True
    assert robot.return_placer_and_prefetch.call_args == call(None)
    assert robot.go_to_standby.called is True
    assert server.motors_locked is False
    assert robot.set_auto_heat_cool_allowed.call_args == call(True)

    update = _get_end_update(server)
    assert update['error'] is None


def test_park_robot_without_dismount(server, robot, make_safe):
    server.park_robot(HANDLE, dismount=False)
    assert robot.park_robot.call_args == call(dismount=False)
    assert make_safe.move_to_safe_position.called is False


def test_park_robot(server, robot, make_safe):

    make_safe_complete = threading.Event()
    make_safe.move_to_safe_position.side_effect = lambda: make_safe_complete.wait()

    park_robot_complete = threading.Event()
    robot.park_robot.side_effect = lambda dismount: park_robot_complete.wait()

    park_robot_thread = threading.Thread(target=server.park_robot, args=(HANDLE,),
                                         kwargs={'dismount': True})
    park_robot_thread.start()
    allow_threads_to_progress()

    # Before starting park operation
    assert robot.set_auto_heat_cool_allowed.call_args == call(False)
    assert make_safe.move_to_safe_position.called is True
    assert robot.prepare_for_mount.called is True
    assert robot.return_placer_and_prefetch.call_args == call(None)
    assert server.motors_locked is True
    robot.return_placer_and_prefetch.reset_mock()
    robot.set_auto_heat_cool_allowed.reset_mock()

    make_safe_complete.set()
    allow_threads_to_progress()

    assert robot.park_robot.called is True
    assert robot.return_placer_and_prefetch.called is False
    assert robot.go_to_standby.called is False
    assert server.motors_locked is True

    park_robot_complete.set()
    park_robot_thread.join()

    assert make_safe.return_positions.called is True
    assert server.motors_locked is False
    assert robot.set_auto_heat_cool_allowed.call_args == call(True)

    update = _get_end_update(server)
    assert update['error'] is None


def test_park_robot_enables_auto_heat_cool_if_makesafe_fails(server, make_safe, robot):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.park_robot(HANDLE, dismount=True)
    assert robot.set_auto_heat_cool_allowed.call_args_list == [call(False), call(True)]


def test_park_robot_unlocks_motors_if_makesafe_fails(server, make_safe, robot):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.park_robot(HANDLE, dismount=True)
    assert robot.goniometer_locked.put.call_args_list == [call(True), call(False)]


def test_dismount_enables_auto_heat_cool_if_makesafe_fails(server, make_safe, robot):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.dismount(HANDLE)
    assert robot.set_auto_heat_cool_allowed.call_args_list == [call(False), call(True)]


def test_dismount_unlocks_motors_if_makesafe_fails(server, make_safe, robot):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.dismount(HANDLE)
    assert robot.goniometer_locked.put.call_args_list == [call(True), call(False)]


def test_dismount_does_nothing_if_no_sample_on_goni(server, robot, make_safe):
    server.robot.goniometer_sample.get.return_value = ''
    server.dismount(HANDLE)
    assert robot.prepare_for_mount.called is False
    assert make_safe.move_to_safe_position.called is False
    update = _get_end_update(server)
    assert update['error'] is None
    assert update['message'] == 'no sample mounted'


def test_mount_and_prefetch_calls_prepare(server, robot, make_safe):
    make_safe_complete = threading.Event()
    make_safe.move_to_safe_position.side_effect = lambda: make_safe_complete.wait()

    mount_complete = threading.Event()
    robot.mount.side_effect = lambda port: mount_complete.wait()

    thread = threading.Thread(target=server.mount_and_prefetch,
                              args=(HANDLE, 'left', 'A', 1, 'right', 'B', 2))
    thread.start()

    # server first runs makesafe and prepares for mount
    allow_threads_to_progress()
    assert robot.set_auto_heat_cool_allowed.call_args == call(False)
    assert make_safe.move_to_safe_position.called is True
    assert robot.prepare_for_mount.called is True
    assert robot.return_placer_and_prefetch.call_args == call(Port('left', 'A', 1))
    assert server.motors_locked is True
    robot.return_placer_and_prefetch.reset_mock()
    robot.set_auto_heat_cool_allowed.reset_mock()

    # until makesafe is complete, robot must not have received mount command
    assert robot.mount.called is False

    # once makesafe is complete we can proceed with mount
    make_safe_complete.set()
    allow_threads_to_progress()
    assert robot.mount.call_args == call(Port('left', 'A', 1))

    # before mount is complete we shouldn't have undone the makesafe
    assert robot.return_placer_and_prefetch.called is False
    assert make_safe.return_positions.called is False
    assert robot.go_to_standby.called is False
    assert server.motors_locked is True

    # once mount is complete, undo-makesafe and return placer can proceed
    mount_complete.set()
    thread.join()

    assert robot.return_placer_and_prefetch.call_args == call(Port('right', 'B', 2))
    assert make_safe.return_positions.called is True
    assert robot.go_to_standby.called is True
    assert server.motors_locked is False
    assert robot.set_auto_heat_cool_allowed.call_args == call(True)

    update = _get_end_update(server)
    assert update['error'] is None


def test_mount_and_prefetch_calls_standby_if_make_safe_fails(server, robot, make_safe):
    make_safe.move_to_safe_position.side_effect = MakeSafeFailed('bad bad happened')
    server.mount_and_prefetch(HANDLE, 'left', 'A', 1, 'right', 'B', 2)
    assert robot.mount.called is False
    assert robot.go_to_standby.called is True
    assert robot.set_auto_heat_cool_allowed.call_args_list == [call(False), call(True)]
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


@pytest.mark.xfail
def test_mount_and_prefetch_goes_to_standby_if_make_safe_return_fails(
        server, robot, make_safe):
    make_safe.return_positions.side_effect = MakeSafeFailed('bad bad happened')
    server.mount_and_prefetch(HANDLE, 'left', 'A', 1, 'right', 'B', 2)
    assert make_safe.return_positions.called is True
    assert robot.prefetch.call_args == call(Port('right', 'B', 2))
    assert robot.go_to_standby.called is True
    update = _get_end_update(server)
    assert update['error'] == 'undo make safe failed: bad bad happened'


@pytest.mark.xfail
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
    assert robot.set_auto_heat_cool_allowed.call_args_list == [call(False), call(True)]
    assert update['error'] is None


def test_prefetch_resets_auto_heat_cool_if_prefetch_fails(server, robot):
    robot.prefetch.side_effect = Exception()
    server.prefetch(HANDLE, 'left', 'A', 1)
    assert robot.set_auto_heat_cool_allowed.call_args_list == [call(False), call(True)]


def test_return_prefetch(server, robot):
    server.return_prefetch(HANDLE)
    assert robot.prepare_for_mount.called is True
    assert robot.return_prefetch.call_args == call()
    assert robot.go_to_standby.called is True
    assert robot.set_auto_heat_cool_allowed.call_args_list == [call(False), call(True)]
    update = _get_end_update(server)
    assert update['error'] is None


def test_return_prefetch_resets_auto_heat_cool_if_return_prefetch_fails(server, robot):
    robot.return_prefetch.side_effect = Exception()
    server.return_prefetch(HANDLE)
    assert robot.set_auto_heat_cool_allowed.call_args_list == [call(False), call(True)]


def test_calibrate_toolset(server, robot):
    server.calibrate_toolset(HANDLE, include_find_magnet=True,
                             quick_mode=False)
    assert robot.calibrate_toolset.call_args == call(include_find_magnet=True,
                                                     quick_mode=False)


def test_calibrate_cassettes(server, robot):
    server.calibrate_cassettes(HANDLE, positions=['left', 'right'], initial=False)
    assert robot.calibrate_cassettes.call_args == call(
        positions=[Position.LEFT, Position.RIGHT], initial=False
    )


def test_calibrate_goniometer_makes_safe_if_not_initial_cal(server, robot, make_safe):
    server.calibrate_goniometer(HANDLE, initial=False)
    assert make_safe.move_to_safe_position.called is True
    assert robot.calibrate_goniometer.call_args == call(initial=False)
    assert make_safe.return_positions.called is True


def test_calibrate_goniometer_makes_safe_if_initial_cal(server, robot, make_safe):
    server.calibrate_goniometer(HANDLE, initial=True)
    assert make_safe.move_to_safe_position.called is False
    assert robot.calibrate_goniometer.call_args == call(initial=True)
    assert make_safe.return_positions.called is False


def test_dry_and_cool(server, robot, make_safe):
    server.dry_and_cool(HANDLE)
    assert robot.dry_and_cool.called
