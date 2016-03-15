import click
from epics import poll
from . import RobotMX, RobotServerMX
import json
import logging.config


@click.command()
@click.option('--config', type=click.Path(exists=True))
@click.argument('robot-name')
def run_server(config, robot_name):
    if config:
        with open(config) as file:
            config = json.load(file)
        if 'logging' in config:
            logging.config.dictConfig(config['logging'])
    robot = RobotMX(robot_name + ':')
    server = RobotServerMX(robot)
    server.setup()
    while True:
        poll()
