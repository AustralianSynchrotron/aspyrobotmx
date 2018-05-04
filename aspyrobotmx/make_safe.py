from urllib.parse import urljoin

import requests


class MakeSafeFailed(Exception):
    """Make safe failed"""


class MakeSafe:
    def __init__(self, base_url):
        self._base_url = base_url

    def move_to_safe_position(self):
        self._execute_request('/makesafe')

    def return_positions(self):
        self._execute_request('/return')

    def _execute_request(self, endpoint):
        response = requests.put(urljoin(self._base_url, endpoint))
        errors = response.json()['errors']
        if len(errors) > 0:
            error = errors[0]
            raise MakeSafeFailed(error.get('message', error['code']))


class DummyMakeSafe:
    def move_to_safe_position(self):
        pass

    def return_positions(self):
        pass
