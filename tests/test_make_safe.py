import responses
import pytest

from aspyrobotmx.make_safe import MakeSafe, MakeSafeFailed


@pytest.fixture
def make_safe():
    yield MakeSafe('http://example.com')


@responses.activate
def test_make_safe_requests_makesafe_endpoint(make_safe):
    responses.add(responses.PUT, 'http://example.com/makesafe',
                  json={'errors': []}, status=200)
    make_safe.move_to_safe_position()
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == 'http://example.com/makesafe'
    assert responses.calls[0].request.method == 'PUT'


@responses.activate
def test_make_safe_raises_exception_if_errors(make_safe):
    responses.add(responses.PUT, 'http://example.com/makesafe',
                  json={'errors': [{'code': 'move-incomplete'}]}, status=200)
    with pytest.raises(MakeSafeFailed):
        make_safe.move_to_safe_position()


@responses.activate
def test_return_positions_requests_return_endpoint(make_safe):
    responses.add(responses.PUT, 'http://example.com/return',
                  json={'errors': []}, status=200)
    make_safe.return_positions()
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == 'http://example.com/return'
    assert responses.calls[0].request.method == 'PUT'


@responses.activate
def test_return_positions_safe_raises_exception_if_errors(make_safe):
    responses.add(responses.PUT, 'http://example.com/return',
                  json={'errors': [{'code': 'move-incomplete'}]}, status=200)
    with pytest.raises(MakeSafeFailed):
        make_safe.return_positions()
