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

    def prepare_for_mount(self):
        return self.run_task('PrepareForMountDismount')

    def mount(self, port):
        return self.run_task('MountSample', port.code)

    def dismount(self, port):
        return self.run_task('DismountSample', port.code)

    def return_placer(self):
        return self.run_task('ReturnPlacerSample')

    def prefetch(self, port):
        return self.run_task('PrefetchSample', port.code)

    def return_placer_and_prefetch(self, port=None):
        code = port.code if port is not None else ''
        return self.run_task('ReturnPlacerPrefetch', code)

    def return_prefetch(self):
        return self.run_task('ReturnPrefetchSample')

    def park_robot(self, *, dismount):
        return self.run_task('ParkRobot', str(int(dismount)))

    def go_to_standby(self):
        return self.run_task('GoStandby')

    def calibrate_toolset(self, *, include_find_magnet, quick_mode):
        args = f'{include_find_magnet:d} {quick_mode:d}'
        return self.run_task('VB_MagnetCal', args)

    def calibrate_cassettes(self, *, positions, initial):
        pos_arg = ''.join([p.code for p in positions])
        args = f'{pos_arg} {initial:d}'
        return self.run_task('VB_CassetteCal', args)

    def calibrate_goniometer(self, *, initial):
        args = f'{initial:d} 0 0 0 0'
        return self.run_task('VB_GonioCal', args)

    def set_auto_heat_cool_allowed(self, value):
        if value:
            self.run_background_task('g_HeatCoolAllowed = -1')
        else:
            self.run_background_task('g_HeatCoolAllowed = 0')
