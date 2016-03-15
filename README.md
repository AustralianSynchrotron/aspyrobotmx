## ASPyRobotMX

Application to control sample mounting robots at the Australian Synchrotron MX
beamlines.

## Testing

An EPICS IOC must be started before running the tests. Ensure EPICS base is
installed and then run:

```
cd tests/fixtures/test-ioc
make
cd iocBoot/iocRobotTestIOC/
./st.cmd
```

The `PYEPICS_LIBCA` environment variable may also need to be set.

Tests can then be run with `tox` or `py.test`:

```
pip install -r requirements.txt
pip install .
py.test
```

## Running

```
pyrobotmxserver --config config.json SR08ID01ROB01
```
