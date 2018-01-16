import json
import logging.config

import click
from epics import poll

from . import RobotMX, RobotServerMX
from .make_safe import MakeSafe


@click.command()
@click.option('--config', type=click.Path(exists=True))
@click.option('--update-address', default='tcp://*:2000')
@click.option('--request-address', default='tcp://*:2001')
@click.option('--make-safe-url', default='http://127.0.0.1:6000')
@click.argument('robot-name')
def run_server(config, update_address, request_address, robot_name, make_safe_url):
    if config:
        with open(config) as file:
            config = json.load(file)
        if 'logging' in config:
            logging.config.dictConfig(config['logging'])
    robot = RobotMX(robot_name + ':')
    make_safe = MakeSafe(make_safe_url)
    server = RobotServerMX(robot, make_safe=make_safe,
                           update_addr=update_address,
                           request_addr=request_address)
    server.setup()
    while True:
        poll(1e-2)
