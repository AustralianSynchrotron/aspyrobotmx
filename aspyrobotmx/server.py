from aspyrobot import RobotServer
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
        instance.publish_queue.put({self.name: value})


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
        self.robot.put('run_args', b'PSDC LMR')
        epics.poll(DELAY_TO_PROCESS)
        self.robot.put('generic_command', b'JSONDataRequest')

    def refresh(self):
        state = self.robot.save_state()
        for attr, pv in self.robot._pvs.items():
            if pv.type == 'ctrl_char':
                state[attr] = pv.char_value
        for attr, obj in RobotServerMX.__dict__.items():
            if isinstance(obj, ServerAttr):
                state[attr] = getattr(self, attr)
        state['height_errors'] = self.height_errors
        state['holder_types'] = self.holder_types
        state['port_states'] = self.port_states
        state['port_distances'] = self.port_distances
        return state

    def update_cassette_type(self, value, position, **_):
        self.holder_types[position] = HOLDER_TYPE_LOOKUP[value]
        self.publish_queue.put({'holder_types': self.holder_types})

    def update_puck_states(self, value, position, start, **_):
        if not value:
            return
        end = start + len(value)
        for slot, state in zip(SLOTS[start:end], value):
            self.puck_states[position][slot] = state
        self.publish_queue.put({'puck_states': self.puck_states})

    def update_port_states(self, value, position, start, **_):
        end = start + len(value)
        self.port_states[position][start:end] = value
        self.publish_queue.put({'port_states': self.port_states})

    def update_sample_distances(self, value, position, start, **_):
        end = start + len(value)
        self.port_distances[position][start:end] = value
        self.publish_queue.put({'port_distances': self.port_distances})

    def update_sample_locations(self, value, **_):
        self.sample_locations = value

    def update_dumbbell_state(self, value, **_):
        # TODO: Test
        self.logger.error('DUMBBELL_STATE: %r', value)

    def set_gripper(self, value):
        self.robot.gripper_command = value

    def set_lid(self, value):
        self.robot.lid_command = value

    def calibrate(self, target, run_args):
        # TODO: Validate args
        self.logger.debug('calibrate target: %r, run_args: %r', target, run_args)
        if target not in {'toolset', 'cassette', 'goniometer'}:
            return {'error': 'invalid target for calibration'}
        if not self.foreground_operation_lock.acquire(False):
            return {'error': 'busy'}
        self.robot.PV('run_args').put(run_args.encode('utf-8'), wait=True)
        self.robot.execute('{target}_calibration'.format(target=target))
        # TODO: Check for errors and release foreground_operation_lock?
        return {'error': None}

    def probe(self, ports):
        # TODO: Validate args
        self.logger.debug('probe ports: %r', ports)
        if not self.foreground_operation_lock.acquire(False):
            return {'error': 'busy'}
        for position in ['left', 'middle', 'right']:
            position_ports = ports[position]
            position_str = ''.join(str(p) for p in position_ports)
            self.robot.put('{position}_probe_request'.format(position=position),
                           position_str.encode('utf-8'), wait=True)
        self.robot.put('generic_command', b'ProbeCassettes', wait=True)
        epics.poll(DELAY_TO_PROCESS)
        if self.robot.foreground_error:
            # TODO: Release foreground_operation_lock?
            return {'error': self.robot.PV('foreground_error_message').char_value}
        return {'error': None}

    def reset_mount_counters(self):
        self.pins_mounted = 0
        self.pins_lost = 0

    def set_holder_type(self, position, type):
        self.holder_types[position] = type
        self.publish_queue.put({'holder_types': self.holder_types})

    def set_port_states(self, position, indices, state):
        # TODO: Should this update SPEL?
        for index in indices:
            self.port_states[position][index] = state
        self.publish_queue.put({'port_states': self.port_states})

    def clear(self):
        self.robot.put('generic_command', b'ClearSamplePositions')

    def prepare_for_mount(self, position, column, port):
        self.logger.info('prepare_for_mount: %r %r %r', position, column, port)
        if self.robot.closest_point != 0:
            return {'error': 'Not at home (near P%s)' % self.robot.closest_point}
        self.robot.put('generic_command', b'JumpHomeToCoolingPoint')

    def mount(self, position, column, port):
        self.logger.info('mount: %r %r %r', position, column, port)
        if self.robot.closest_point != 3:
            error = 'Not at cooling point (near P%s)' % self.robot.closest_point
            return {'error': error}
        args = '{} {} {}'.format(position[0], column, port).upper()
        self.robot.put('run_args', args.encode('utf-8'))
        epics.poll(DELAY_TO_PROCESS)
        self.robot.put('generic_command', b'MountSamplePort')

    def dismount(self, position, column, port):
        self.logger.info('prepare_for_dismount: %r %r %r', position, column, port)
        if self.robot.closest_point != 3:
            error = 'Not at cooling point (near P%s)' % self.robot.closest_point
            return {'error': error}
        args = '{} {} {}'.format(position[0], column, port).upper()
        self.robot.put('run_args', args.encode('utf-8'))
        epics.poll(DELAY_TO_PROCESS)
        self.robot.put('generic_command', b'DismountSample')
