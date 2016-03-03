from aspyrobot import Robot


class RobotMX(Robot):
    attrs = Robot.attrs
    attrs.update({
        'lid_open': 'LIDOPEN_STATUS',
        'lid_closed': 'LIDCLOSE_STATUS',
        'lid_command': 'LID_CMD',
        'gripper_open': 'GRIPOPEN_STATUS',
        'gripper_closed': 'GRIPCLOSE_STATUS',
        'gripper_command': 'GRIP_CMD',
        'toolset_calibration': 'VBMC_CMD',
        'cassette_calibration': 'VBCC_CMD',
        'goniometer_calibration': 'VBGC_CMD',
        'left_probe_request': 'PROBELEFTREQUEST_CMD',
        'middle_probe_request': 'PROBEMIDDLEREQUEST_CMD',
        'right_probe_request': 'PROBERIGHTREQUEST_CMD',
        'ln2_level': 'LN2LEVEL_STATUS',
    })
    attrs_r = {v: k for k, v in attrs.items()}
