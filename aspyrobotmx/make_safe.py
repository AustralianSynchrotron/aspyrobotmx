from urllib.parse import urljoin

import requests


class MakeSafeFailed(Exception):
    """Make safe failed"""


class MakeSafe:
    def __init__(self, base_url):
        self._base_url = base_url

    def move_to_safe_position(self):
        response = requests.put(urljoin(self._base_url, '/makesafe'))
        errors = response.json()['errors']
        if len(errors) > 0:
            raise MakeSafeFailed(errors[0]['message'])

    def return_positions(self):
        response = requests.put(urljoin(self._base_url, '/return'))
        errors = response.json()['errors']
        if len(errors) > 0:
            raise MakeSafeFailed(errors[0]['message'])
