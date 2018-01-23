from itertools import repeat
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple
from enum import Enum


from aspyrobot import RobotServer
from aspyrobot.server import (foreground_operation, background_operation,
                              query_operation)
from aspyrobot.exceptions import RobotError
from epics import poll

from .codes import HolderType, PuckState, PortState, SampleState
from .make_safe import MakeSafeFailed


POSITIONS = ['left', 'middle', 'right']
SLOTS = ['A', 'B', 'C', 'D']
PORTS_PER_POSITION = 96
DELAY_TO_PROCESS = .5


class ServerAttr(object):
    def __init__(self, name, default=None):
        self.name = name
        self.default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, '_' + self.name, self.default)

    def __set__(self, instance, value):
        setattr(instance, '_' + self.name, value)
        instance.values_update({self.name: value})


class RobotServerMX(RobotServer):
    """
    A subclass of ``aspyrobot.RobotServer`` with extra functionality for the
    sample mounting robots at the MX beamlines of the Australian Synchrotron.
    Adds operations for calibrating, probing and mounting samples.

    Args:
        robot (RobotMX): An instance of RobotMX to enable communication with the
            robot EPICS IOC.
        **kwargs: Extra keyword parameters to be passed to RobotServer.

    """
    pins_mounted = ServerAttr('pins_mounted', 0)
    pins_lost = ServerAttr('pins_lost', 0)
    sample_locations = ServerAttr('sample_locations', {
        'cavity': None, 'picker': None, 'placer': None, 'goniometer': None
    })
    dumbbell_state = ServerAttr('dumbbell_state')
    mount_message = ServerAttr('mount_message', default='')

    def __init__(self, robot, *, make_safe, **kwargs):
        super().__init__(robot, **kwargs)
        self.logger.debug('__init__')
        self.make_safe = make_safe
        self.height_errors = {'left': None, 'middle': None, 'right': None}
        self.holder_types = dict.fromkeys(POSITIONS, HolderType.unknown)
        pucks_unknown = dict.fromkeys(SLOTS, int(PuckState.unknown))
        self.puck_states = {'left': deepcopy(pucks_unknown),
                            'middle': deepcopy(pucks_unknown),
                            'right': deepcopy(pucks_unknown)}
        ports_unknown = list(repeat(int(PortState.unknown), PORTS_PER_POSITION))
        self.port_states = {'left': deepcopy(ports_unknown),
                            'middle': deepcopy(ports_unknown),
                            'right': deepcopy(ports_unknown)}
        port_distances_unknown = list(repeat(None, PORTS_PER_POSITION))
        self.port_distances = {
            'left': deepcopy(port_distances_unknown),
            'middle': deepcopy(port_distances_unknown),
            'right': deepcopy(port_distances_unknown),
        }
        self.motors_locked = False

    def setup(self):
        super(RobotServerMX, self).setup()
        self.fetch_all_data()

    def fetch_all_data(self):
        self.robot.task_args.put('PSDC LMR')
        poll(DELAY_TO_PROCESS)
        self.robot.generic_command.put('DataRequest')

    def lock_motors(self):
        self.motors_locked = True
        self.values_update({'motors_locked': self.motors_locked})

    def free_motors(self):
        self.motors_locked = False
        self.values_update({'motors_locked': self.motors_locked})

    # ******************************************************************
    # ************************ Updates ******************************
    # ******************************************************************

    def update_cassette_type(self, value, position, **_):
        self.holder_types[position] = HolderType[value]
        self.values_update({'holder_types': self.holder_types})

    def update_puck_states(self, value, position, start, **_):
        if not value:
            return
        end = start + len(value)
        for slot, state in zip(SLOTS[start:end], value):
            self.puck_states[position][slot] = state
        self.values_update({'puck_states': self.puck_states})

    def update_adaptor_puck_status(self, value, position, puck, **_):
        self.puck_states[position][puck] = int(value)
        self.values_update({'puck_states': self.puck_states})

    def update_port_states(self, value, position, start, **_):
        end = start + len(value)
        self.port_states[position][start:end] = value
        self.values_update({'port_states': self.port_states})

    def update_sample_distances(self, value, position, start, **_):
        end = start + len(value)
        self.port_distances[position][start:end] = value
        self.values_update({'port_distances': self.port_distances})

    def update_sample_locations(self, value, **_):
        self.sample_locations = value

    def update_magnet_state(self, value, **_):
        self.dumbbell_state = value

    def update_mount_message(self, value, **_):
        self.mount_message = value

    # ******************************************************************
    # ****************** High Level Operations *************************
    # ******************************************************************

    @foreground_operation
    def mount(self, handle, position, column, port_num):
        self.logger.info(f'mount: {position} {column} {port_num}')
        port = Port(position, column, port_num)
        try:
            self.robot.set_auto_heat_cool_allowed(False)
            self.lock_motors()
            self._prepare_for_mount_and_make_safe(handle, port=port)
            self.robot.mount(port)
            self.free_motors()
            self._undo_make_safe_and_finalise_robot(handle)
        finally:
            self.robot.set_auto_heat_cool_allowed(True)

    @foreground_operation
    def mount_and_prefetch(self, handle, position, column, port_num,
                           prefetch_position, prefetch_column, prefetch_port_num):
        # TODO: Handle make safe timeout
        # TODO: Handle exceptions other than RobotError and MakeSafeFailed
        mount_port = Port(position, column, port_num)
        prefetch_port = Port(prefetch_position, prefetch_column, prefetch_port_num)
        try:
            self.robot.set_auto_heat_cool_allowed(False)
            self.lock_motors()
            self._prepare_for_mount_and_make_safe(handle, port=mount_port)
            self.robot.mount(mount_port)
            self.free_motors()
            self._undo_make_safe_and_finalise_robot(handle, prefetch_port)
        finally:
            self.robot.set_auto_heat_cool_allowed(True)

    @foreground_operation
    def dismount(self, handle):
        port_code = self.robot.goniometer_sample.get().strip()
        if not port_code:
            return 'no sample mounted'
        try:
            self.robot.set_auto_heat_cool_allowed(False)
            self.lock_motors()
            port = Port.from_code(port_code)
            self._prepare_for_mount_and_make_safe(handle)
            self.operation_update(handle, message='dismounting {port}')
            self.robot.dismount(port)
            self.free_motors()
            self._undo_make_safe_and_finalise_robot(handle)
        finally:
            self.robot.set_auto_heat_cool_allowed(True)

    @foreground_operation
    def prefetch(self, handle, position, column, port_num):
        try:
            self.robot.set_auto_heat_cool_allowed(False)
            self.robot.prepare_for_mount()
            self.robot.prefetch(Port(position, column, port_num))
            self.robot.go_to_standby()
        finally:
            self.robot.set_auto_heat_cool_allowed(True)

    @foreground_operation
    def return_prefetch(self, handle):
        try:
            self.robot.set_auto_heat_cool_allowed(False)
            self.robot.prepare_for_mount()
            self.robot.return_prefetch()
            self.robot.go_to_standby()
        finally:
            self.robot.set_auto_heat_cool_allowed(True)

    def _prepare_for_mount_and_make_safe(self, handle, *, port=None):
        with ThreadPoolExecutor(max_workers=2) as executor:
            prepare_future = executor.submit(self._prepare_and_prefetch, port)
            make_safe_future = executor.submit(self.make_safe.move_to_safe_position)
            prepare_future.result()
            try:
                make_safe_future.result()
            except MakeSafeFailed as exc:
                self.robot.go_to_standby()
                raise RobotError(f'make safe failed: {exc}') from exc

    def _prepare_and_prefetch(self, prefetch_port=None):
        self.robot.prepare_for_mount()
        self.robot.return_placer_and_prefetch(prefetch_port)

    def _undo_make_safe_and_finalise_robot(self, handle, prefetch_port=None):

        def prefetch_and_go_standby():
            self.operation_update(handle, message='returning placer and prefetching')
            self.robot.return_placer_and_prefetch(prefetch_port)
            self.operation_update(handle, message='going to standby position')
            self.robot.go_to_standby()

        with ThreadPoolExecutor(max_workers=2) as executor:

            undo_make_safe_future = executor.submit(self.make_safe.return_positions)
            prefetch_and_go_standby_future = executor.submit(prefetch_and_go_standby)

            try:
                prefetch_and_go_standby_future.result()
            except RobotError as exc:
                robot_exc = exc
            else:
                robot_exc = None

            try:
                undo_make_safe_future.result()
            except MakeSafeFailed as exc:
                self.operation_update(handle, error=str(exc))
                make_safe_exc = RobotError(f'undo make safe failed: {exc}')
            else:
                make_safe_exc = None

            final_exc = robot_exc or make_safe_exc
            if final_exc:
                raise final_exc

    # ******************************************************************
    # ************************ Operations ******************************
    # ******************************************************************

    @query_operation
    def refresh(self):
        state = self.robot.snapshot()
        for attr, obj in RobotServerMX.__dict__.items():
            if isinstance(obj, ServerAttr):
                state[attr] = getattr(self, attr)
        state['height_errors'] = self.height_errors
        state['holder_types'] = self.holder_types
        state['port_states'] = self.port_states
        state['port_distances'] = self.port_distances
        state['motors_locked'] = self.motors_locked
        return state

    @background_operation
    def set_gripper(self, handle, value):
        self.robot.gripper_command.put(value)

    @background_operation
    def set_lid(self, handle, value):
        self.robot.lid_command.put(value)

    @background_operation
    def set_heater(self, handle, value):
        self.robot.heater_command.put(value)

    @background_operation
    def set_heater_air(self, handle, value):
        self.robot.heater_air_command.put(value)

    @foreground_operation
    def calibrate_toolset(self, handle, *, include_find_magnet, quick_mode):
        # TODO: Validate args
        self.logger.debug('calibrate toolset: %r %r', include_find_magnet, quick_mode)
        message = self.robot.calibrate_toolset(include_find_magnet=include_find_magnet,
                                               quick_mode=quick_mode)
        self.logger.info('calibrate message: %r', message)
        return message

    @foreground_operation
    def calibrate_cassettes(self, handle, *, positions, initial):
        self.logger.debug('calibrate cassettes: %r %r', positions, initial)
        positions = [Position(p) for p in positions]
        message = self.robot.calibrate_cassettes(positions=positions, initial=initial)
        self.logger.info('calibrate message: %r', message)
        return message

    @foreground_operation
    def calibrate_goniometer(self, handle, *, initial):
        # TODO: Validate args
        self.logger.debug('calibrate goniometer: %r', initial)
        if not initial:
            self.make_safe.move_to_safe_position()
        message = self.robot.calibrate_goniometer(initial=initial)
        if not initial:
            self.make_safe.return_positions()
        self.logger.info('calibrate message: %r', message)
        return message

    @foreground_operation
    def probe(self, handle, ports):
        # TODO: Validate args
        self.logger.debug('probe ports: %r', ports)
        self.set_probe_requests(ports)
        poll(DELAY_TO_PROCESS)
        message = self.robot.run_task('ProbeCassettes')
        self.logger.info('probe message: %r', message)
        return message

    @background_operation
    def reset_mount_counters(self, handle):
        self.pins_mounted = 0
        self.pins_lost = 0

    @background_operation
    def set_port_state(self, handle, position, column, port_num, state):
        self.logger.error('%r %r %r %r', position, column, port_num, state)
        args = '{} {} {} {}'.format(position[0], column, port_num, state).upper()
        message = self.robot.run_task('SetPortState', args)
        self.logger.info('message: %r', message)
        return message

    @background_operation
    def reset_holders(self, handle, positions):
        task_args = ''.join(position[0].upper() for position in positions)
        self.robot.run_task('ResetCassettes', task_args)

    @background_operation
    def reset_ports(self, handle, ports):
        self.set_probe_requests(ports)
        poll(DELAY_TO_PROCESS)
        message = self.robot.run_task('ResetCassettePorts')
        self.logger.info('message: %r', message)
        return message

    @background_operation
    def inspected(self, handle):
        self.free_motors()
        message = self.robot.run_task('Inspected')
        self.logger.info('message: %r', message)
        return message

    @background_operation
    def set_sample_state(self, handle, position, column, port_num, state):
        self.logger.info('set_sample_state: %r %r %r %r',
                         position, column, port_num, state)
        state = SampleState(state).name
        # TODO: This should be fixed in SPEL
        port_code = Port(position, column, port_num).code.replace(' ', '')
        task_args = '{} {}'.format(port_code, state)
        self.robot.run_background_task('SetSampleStatus', task_args)

    # ******************************************************************
    # ********************* Helper methods *****************************
    # ******************************************************************

    def set_probe_requests(self, ports):
        for position in ['left', 'middle', 'right']:
            position_ports = ports.get(position, [])
            position_ports_str = ''.join(str(p) for p in position_ports)
            pv = getattr(self.robot, '{pos}_probe_request'.format(pos=position))
            pv.put(position_ports_str)


class Port(NamedTuple):

    position: str
    column: str
    port_num: int

    @property
    def code(self):
        return f'{self.position[0]} {self.column} {self.port_num}'.upper()

    @classmethod
    def from_code(cls, code):
        pos_char, column, port_num = code.split(' ')
        position = {'l': 'left', 'r': 'right', 'm': 'middle'}[pos_char.lower()]
        return cls(position, column, int(port_num))


class Position(Enum):

    LEFT = 'left'
    MIDDLE = 'middle'
    RIGHT = 'right'

    @property
    def code(self):
        return self.value[0]
