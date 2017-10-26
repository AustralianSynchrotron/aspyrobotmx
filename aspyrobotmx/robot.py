from aspyrobot import Robot


class RobotMX(Robot):
    """
    ``RobotMX`` subclasses ``aspyrobot.Robot`` to add additional ``PV``\ s for
    hardware I/O such as the robot gripper, dewar lid and heater.
    """

    attrs = Robot.attrs
    attrs.update({
        'lid_open': 'LIDOPEN_STATUS',
        'lid_closed': 'LIDCLOSE_STATUS',
        'lid_command': 'LID_CMD',
        'gripper_open': 'GRIPOPEN_STATUS',
        'gripper_closed': 'GRIPCLOSE_STATUS',
        'gripper_command': 'GRIP_CMD',
        'left_probe_request': 'PROBELEFTREQUEST_CMD',
        'middle_probe_request': 'PROBEMIDDLEREQUEST_CMD',
        'right_probe_request': 'PROBERIGHTREQUEST_CMD',
        'ln2_level': 'LN2LEVEL_STATUS',
        'heater_hot': 'HEATER_STATUS',
        'heater_command': 'HEATER_CMD',
        'heater_air_command': 'DRYAIR_CMD',
        'last_toolset_calibration': 'TCTS_MON',
        'last_left_calibration': 'LCCTS_MON',
        'last_middle_calibration': 'MCCTS_MON',
        'last_right_calibration': 'RCCTS_MON',
        'last_goniometer_calibration': 'GCTS_MON',
        'picker_sample': 'PICKERSAMPLE_MON',
        'placer_sample': 'PLACERSAMPLE_MON',
        'cavity_sample': 'CAVITYSAMPLE_MON',
        'goniometer_sample': 'GONIOSAMPLE_MON',
    })
    attrs_r = {v: k for k, v in attrs.items()}
