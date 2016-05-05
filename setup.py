from setuptools import setup
import re

with open('aspyrobotmx/__init__.py', 'r') as f:
    version = re.search(r"__version__ = '(.*)'", f.read()).group(1)

setup(
    name='aspyrobotmx',
    version=version,
    maintainer='Robbie Clarken',
    maintainer_email='robbie.clarken@synchrotron.org.au',
    url='https://github.com/AustralianSynchrotron/aspyrobotmx',
    license='MIT',
    packages=['aspyrobotmx'],
    install_requires=[
        'aspyrobot',
        'click',
        'colorlog',
    ],
    entry_points={
        'console_scripts': [
            'pyrobotmxserver=aspyrobotmx.cmd:run_server'
        ],
    },
)
