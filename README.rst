ASPyRobotMX
-----------

Application to control sample mounting robots at the Australian
Synchrotron MX beamlines.

.. image:: https://readthedocs.org/projects/aspyrobotmx/badge/?version=latest
   :target: http://aspyrobotmx.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

Documentation is available at `<http://aspyrobotmx.readthedocs.io>`_.

Testing
-------

The EPICS IOC in `<https://github.com/AustralianSynchrotron/robotmx-testioc>`_
must be started before running the tests.

Tests can then be run with ``tox`` or ``pytest``::

    pip install -r requirements-dev.txt
    pip install .
    pytest --forked

Running
-------

::

    pyrobotmxserver --config config.json SR08ID01ROB01
