import pytest

from aspyrobotmx.server import RobotServerMX
from aspyrobotmx.codes import HolderType, PuckState, PortState, DumbbellState


UPDATE_ADDR = 'tcp://127.0.0.1:3000'
REQUEST_ADDR = 'tcp://127.0.0.1:3001'


@pytest.yield_fixture
def server():
    yield RobotServerMX(robot=None, update_addr=UPDATE_ADDR,
                        request_addr=REQUEST_ADDR)


def test_update_cassette_type(server):
    server.update_cassette_type(value='calibration', position='left',
                                min_height_error=0.123)
    assert server.holder_types['left'] == HolderType.calibration
    assert 'holder_types' in server.publish_queue.get_nowait()['data']


def test_update_puck_states(server):
    server.update_puck_states(value=[1, 1, -1, 1], position='middle', start=0)
    assert server.puck_states['middle']['A'] == PuckState.empty
    assert server.puck_states['middle']['C'] == PuckState.full
    assert 'puck_states' in server.publish_queue.get_nowait()['data']


def test_update_adaptor_puck_status(server):
    # HACK: This update needs to be replaced in SPEL with the puck_states message
    server.update_adaptor_puck_status(value='-1', position='middle', puck='C')
    assert server.puck_states['middle']['C'] == PuckState.full
    assert 'puck_states' in server.publish_queue.get_nowait()['data']


def test_update_port_states(server):
    server.update_port_states(value=[-1], position='left', start=0)
    assert server.port_states['left'][0] == PortState.full
    assert 'port_states' in server.publish_queue.get_nowait()['data']


def test_update_sample_distances(server):
    server.update_sample_distances(value=[-1.2, -3.4], position='left', start=0)
    assert server.port_distances['left'][0] == -1.2
    assert server.port_distances['left'][1] == -3.4
    assert 'port_distances' in server.publish_queue.get_nowait()['data']


def test_update_sample_locations(server):
    server.update_sample_locations(value={
        'cavity': ('left', 0),
        'picker': (),
        'placer': (),
        'goniometer': (),
    })
    assert server.sample_locations['cavity'] == ('left', 0)
    assert 'sample_locations' in server.publish_queue.get_nowait()['data']


def test_update_magnet_state(server):
    server.update_magnet_state(value=1)
    update = server.publish_queue.get_nowait()
    update_value = update['data']['dumbbell_state']
    assert update_value == DumbbellState.in_cradle
