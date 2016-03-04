import click
from epics import poll
from . import RobotMX, RobotServerMX


@click.command()
@click.argument('robot-name')
def run_server(robot_name):
    robot = RobotMX(robot_name + ':')
    server = RobotServerMX(robot)
    server.setup()
    while True:
        poll()
