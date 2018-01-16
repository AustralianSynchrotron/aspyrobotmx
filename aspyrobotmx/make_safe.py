from urllib.parse import urljoin

import requests


class MakeSafeFailed(Exception):
    """Make safe failed"""


class MakeSafe:
    def __init__(self, base_url):
        self._base_url = base_url

    def move_to_safe_position(self):
        response = requests.put(urljoin(self._base_url, '/makesafe'))
        if len(response.json()['errors']) > 0:
            raise MakeSafeFailed('make safe failed')

    def return_positions(self):
        response = requests.put(urljoin(self._base_url, '/return'))
        if len(response.json()['errors']) > 0:
            raise MakeSafeFailed('return positions failed')
