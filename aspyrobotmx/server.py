from itertools import repeat
from threading import Event
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor


from aspyrobot import RobotServer
from aspyrobot.server import (foreground_operation, background_operation,
                              query_operation)
from aspyrobot.exceptions import RobotError
from epics import poll
from epics.ca import CAThread

from .codes import HolderType, PuckState, PortState, SampleState
from .make_safe import MakeSafeFailed


POSITIONS = ['left', 'middle', 'right']
SLOTS = ['A', 'B', 'C', 'D']
PORTS_PER_POSITION = 96
DELAY_TO_PROCESS = .5
PREPARE_TIMEOUT = 240


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
        super(RobotServerMX, self).__init__(robot, **kwargs)
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
        self._abort_prepare_timeout = Event()
        self._prepared_for_mount = False

    def setup(self):
        super(RobotServerMX, self).setup()
        self.fetch_all_data()

    def fetch_all_data(self):
        self.robot.task_args.put('PSDC LMR')
        poll(DELAY_TO_PROCESS)
        self.robot.generic_command.put('DataRequest')

    # ******************************************************************
    # ************************ Updates ******************************
    # ******************************************************************

    def update_cassette_type(self, value, position, **_):
        holder_type = HolderType[value]
        self.holder_types[position] = holder_type
        update = {'holder_types': self.holder_types}
        if holder_type == HolderType.unknown:
            # TODO: This should be triggered by SPEL updates but the
            # puck_states and port_states updates from ResetCassettes
            # were empty lists for some reason.
            for puck in 'ABCD':
                self.puck_states[position][puck] = PuckState.unknown
            for port in range(PORTS_PER_POSITION):
                self.port_states[position][port] = PortState.unknown
            update['puck_states'] = self.puck_states
            update['port_states'] = self.port_states
        self.values_update(update)

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
    def mount_and_premount(self, handle, position, column, port,
                           premount_position, premount_column, premount_port):

        # TODO: Handle exceptions other than RobotError and MakeSafeFailed

        with ThreadPoolExecutor(max_workers=2) as executor:
            prepare_future = executor.submit(self._prepare_for_mount, handle)
            make_safe_future = executor.submit(self.make_safe.move_to_safe_position)
            prepare_future.result()
            try:
                make_safe_future.result()
            except MakeSafeFailed as exc:
                self._go_to_standby(handle)
                raise RobotError(f'make safe failed: {exc}') from exc
        self._mount(handle, position, column, port)

        def prefetch_and_go_standby():
            self._return_placer(handle)
            self._go_to_standby(handle)
            # TODO: Check this is correct
            self._prefetch(handle, premount_position, premount_column, premount_port)
            self._go_to_standby(handle)

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
    def calibrate(self, handle, target, task_args):
        # TODO: Validate args
        self.logger.debug('calibrate target: %r, task_args: %r', target, task_args)
        if target == 'toolset':
            cmd = 'VB_MagnetCal'
        elif target == 'cassette':
            cmd = 'VB_CassetteCal'
        elif target == 'goniometer':
            cmd = 'VB_GonioCal'
        else:
            raise RobotError('invalid target for calibration')
        message = self.robot.run_task(cmd, task_args)
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
    def set_port_state(self, handle, position, column, port, state):
        self.logger.error('%r %r %r %r', position, column, port, state)
        args = '{} {} {} {}'.format(position[0], column, port, state).upper()
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
        message = self.robot.run_task('Inspected')
        self.logger.info('message: %r', message)
        return message

    @background_operation
    def set_sample_state(self, handle, position, column, port, state):
        self.logger.info('set_sample_state: %r %r %r %r',
                         position, column, port, state)
        state = SampleState(state).name
        port_code = '{}{}{}'.format(position[0], column, port).upper()
        task_args = '{} {}'.format(port_code, state)
        self.robot.run_background_task('SetSampleStatus', task_args)

    # ******************************************************************
    # ******************* Internal Operations **************************
    # ******************************************************************

    def _prepare_for_mount(self, handle):
        self.logger.info('prepare_for_mount')
        message = self.robot.run_task('PrepareForMountDismount')
        self.logger.info('message: %r', message)
        self._prepared_for_mount = True
        self._start_prepare_timeout(PREPARE_TIMEOUT)
        return message

    def _mount(self, handle, position, column, port):
        self.logger.info('mount: %r %r %r', position, column, port)
        if not self._prepared_for_mount:
            raise RobotError('run prepare_for_mount first')
        self._abort_prepare_timeout.set()
        port_code = '{} {} {}'.format(position[0], column, port).upper()
        spel_operation = 'MountSamplePort'
        message = self.robot.run_task(spel_operation, port_code)
        self.logger.info('message: %r', message)
        return message

    def _dismount(self, handle, position, column, port):
        self.logger.info('prepare_for_dismount: %r %r %r', position, column, port)
        if not self._prepared_for_mount:
            raise RobotError('run prepare_for_mount first')
        self._abort_prepare_timeout.set()
        port_code = '{} {} {}'.format(position[0], column, port).upper()
        message = self.robot.run_task('DismountSample', port_code)
        self.logger.info('message: %r', message)
        return message

    def _return_placer(self, handle):
        message = 'TODO'
        return message

    def _prefetch(self, handle, position, column, port):
        message = 'TODO'
        return message

    def _go_to_standby(self, handle):
        self.logger.debug('sending robot to standby')
        message = self.robot.run_task('GoStandby')
        self.logger.info('message: %r', message)
        return message

    # ******************************************************************
    # ********************* Helper methods *****************************
    # ******************************************************************

    def _start_prepare_timeout(self, timeout):
        self._abort_prepare_timeout.clear()
        CAThread(target=self._prepare_timeout, args=(timeout,), daemon=True).start()

    def _prepare_timeout(self, timeout):
        self.logger.debug('waiting %s seconds for next operation to start', timeout)
        if not self._abort_prepare_timeout.wait(timeout):
            self._prepared_for_mount = False
            self.logger.warning('timed out at cooling point. going home')
            self.robot.run_task('GoHomeDueToError')
        else:
            self.logger.debug('operation detected. timeout aborted')

    def set_probe_requests(self, ports):
        for position in ['left', 'middle', 'right']:
            position_ports = ports.get(position, [])
            position_ports_str = ''.join(str(p) for p in position_ports)
            pv = getattr(self.robot, '{pos}_probe_request'.format(pos=position))
            pv.put(position_ports_str)
