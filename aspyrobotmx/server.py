from aspyrobot import RobotServer
from aspyrobot.server import (foreground_operation, background_operation,
                              query_operation)
from aspyrobot.exceptions import RobotError

import epics
from itertools import repeat


# TODO: Make these match SPEL
HOLDER_TYPE_UNKNOWN = 'u'
HOLDER_TYPE_CASSETTE = '1'
HOLDER_TYPE_CALIBRATION_CASSETTE = '2'
HOLDER_TYPE_ADAPTOR = '3'
HOLDER_TYPE_ERROR = 'X'

HOLDER_TYPE_LOOKUP = {
    'unknown': HOLDER_TYPE_UNKNOWN,
    'calibration': HOLDER_TYPE_CALIBRATION_CASSETTE,
    'normal': HOLDER_TYPE_CASSETTE,
    'superpuck': HOLDER_TYPE_ADAPTOR,
}

PUCK_STATE_FULL = -1
PUCK_STATE_UNKNOWN = 0
PUCK_STATE_EMPTY = 1
PUCK_STATE_ERROR = 2

PORT_STATE_FULL = -1
PORT_STATE_UNKNOWN = 0
PORT_STATE_EMPTY = 1
PORT_STATE_ERROR = 2

SAMPLE_STATE_UNKNOWN = 0
SAMPLE_STATE_IN_CASSETTE = 1
SAMPLE_STATE_IN_PICKER = 2
SAMPLE_STATE_IN_PLACER = 3
SAMPLE_STATE_IN_CRADLE = 4
SAMPLE_STATE_IN_CAVITY = 5
SAMPLE_STATE_IN_GONIOMETER = 6

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

    pins_mounted = ServerAttr('pins_mounted', 0)
    pins_lost = ServerAttr('pins_lost', 0)
    sample_locations = ServerAttr('sample_locations', {
        'cavity': None, 'picker': None, 'placer': None, 'goniometer': None
    })
    last_toolset_calibration = ServerAttr('last_toolset_calibration')
    last_left_calibration = ServerAttr('last_left_calibration')
    last_middle_calibration = ServerAttr('last_middle_calibration')
    last_right_calibration = ServerAttr('last_right_calibration')
    last_goniometer_calibration = ServerAttr('last_goniometer_calibration')

    def __init__(self, robot, **kwargs):
        super(RobotServerMX, self).__init__(robot, **kwargs)
        self.logger.debug('__init__')
        self.height_errors = {'left': None, 'middle': None, 'right': None}
        self.holder_types = dict.fromkeys(POSITIONS, HOLDER_TYPE_UNKNOWN)
        self.puck_states = {
            'left': dict.fromkeys(SLOTS, PUCK_STATE_UNKNOWN),
            'middle': dict.fromkeys(SLOTS, PUCK_STATE_UNKNOWN),
            'right': dict.fromkeys(SLOTS, PUCK_STATE_UNKNOWN),
        }
        self.port_states = {
            'left': list(repeat(PORT_STATE_UNKNOWN, PORTS_PER_POSITION)),
            'middle': list(repeat(PORT_STATE_UNKNOWN, PORTS_PER_POSITION)),
            'right': list(repeat(PORT_STATE_UNKNOWN, PORTS_PER_POSITION)),
        }
        self.port_distances = {
            'left': list(repeat(None, PORTS_PER_POSITION)),
            'middle': list(repeat(None, PORTS_PER_POSITION)),
            'right': list(repeat(None, PORTS_PER_POSITION)),
        }

    def setup(self):
        super(RobotServerMX, self).setup()
        self.fetch_all_data()

    def fetch_all_data(self):
        self.robot.run_args.put('PSDC LMR')
        epics.poll(DELAY_TO_PROCESS)
        self.robot.generic_command.put('JSONDataRequest')

    # ******************************************************************
    # ************************ Updates ******************************
    # ******************************************************************

    def update_cassette_type(self, value, position, **_):
        self.holder_types[position] = HOLDER_TYPE_LOOKUP[value]
        self.values_update({'holder_types': self.holder_types})

    def update_puck_states(self, value, position, start, **_):
        if not value:
            return
        end = start + len(value)
        for slot, state in zip(SLOTS[start:end], value):
            self.puck_states[position][slot] = state
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

    def update_dumbbell_state(self, value, **_):
        # TODO: Test
        self.logger.error('DUMBBELL_STATE: %r', value)

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

    @foreground_operation
    def calibrate(self, handle, target, run_args):
        # TODO: Validate args
        self.logger.debug('calibrate target: %r, run_args: %r', target, run_args)
        if target == 'toolset':
            cmd = 'VB_MagnetCal'
        elif target == 'cassette':
            cmd = 'VB_CassetteCal'
        elif target == 'goniometer':
            cmd = 'VB_GonioCal'
        else:
            raise RobotError('invalid target for calibration')
        message = self.robot.run_foreground_operation(cmd, run_args)
        self.logger.info('calibrate message: %r', message)
        return message

    @foreground_operation
    def probe(self, handle, ports):
        # TODO: Validate args
        self.logger.debug('probe ports: %r', ports)
        self.set_probe_requests(ports)
        epics.poll(DELAY_TO_PROCESS)
        message = self.robot.run_foreground_operation('ProbeCassettes')
        self.logger.info('probe message: %r', message)
        return message

    @background_operation
    def reset_mount_counters(self, handle):
        self.pins_mounted = 0
        self.pins_lost = 0

    @background_operation
    def set_holder_type(self, handle, position, type):
        # TODO: Should call SPEL function
        pass

    @background_operation
    def set_port_state(self, handle, position, column, port, state):
        self.logger.error('%r %r %r %r', position, column, port, state)
        args = '{} {} {} {}'.format(position[0], column, port, state).upper()
        message = self.robot.run_foreground_operation('SetPortState', args)
        self.logger.info('message: %r', message)
        return message

    @background_operation
    def reset_ports(self, handle, ports):
        self.set_probe_requests(ports)
        epics.poll(DELAY_TO_PROCESS)
        message = self.robot.run_foreground_operation('ResetCassettePorts')
        self.logger.info('message: %r', message)
        return message

    @foreground_operation
    def prepare_for_mount(self, handle):
        self.logger.info('prepare_for_mount')
        message = self.robot.run_foreground_operation('PrepareForMountDismount')
        self.logger.info('message: %r', message)
        return message

    @foreground_operation
    def mount(self, handle, position, column, port):
        self.logger.info('mount: %r %r %r', position, column, port)
        port_code = '{} {} {}'.format(position[0], column, port).upper()
        spel_operation = 'MountSamplePortAndGoHome'
        message = self.robot.run_foreground_operation(spel_operation, port_code)
        self.logger.info('message: %r', message)
        return message

    @foreground_operation
    def dismount(self, handle, position, column, port):
        self.logger.info('prepare_for_dismount: %r %r %r', position, column, port)
        port_code = '{} {} {}'.format(position[0], column, port).upper()
        message = self.robot.run_foreground_operation('DismountSample', port_code)
        self.logger.info('message: %r', message)
        return message

    # ******************************************************************
    # ********************* Helper methods *****************************
    # ******************************************************************

    def set_probe_requests(self, ports):
        for position in ['left', 'middle', 'right']:
            position_ports = ports.get(position, [])
            position_ports_str = ''.join(str(p) for p in position_ports)
            pv = getattr(self.robot, '{pos}_probe_request'.format(pos=position))
            pv.put(position_ports_str)
