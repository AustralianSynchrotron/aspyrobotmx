from aspyrobot import RobotClient


class RobotClientMX(RobotClient):
    """
    ``RobotClientMX`` subclasses ``aspyrobot.RobotClient`` to add attributes and
    methods specific to the MX application. These include operation methods to
    calibrate, probe and mount samples.

    Attributes:
        current_task (str): Current task being executed on the robot
        task_message (str): Messages about current foreground task
        task_progress (str): Current task progress
        status (int): Status flag of the robot: bitwise or of codes.RobotStatus
        model (str): Model of the robot
        time (str): Time on robot controller (can be used as a heartbeat monitor)
        at_home (int): Whether the robot is in the home position
        motors_on (int): Whether the robot motors are on
        motors_on_command (int): Value of motors on instruction
        toolset (codes.Toolset): Current toolset the robot is in
        foreground_done (int): Whether the foreground is available
        safety_gate (int): Is the safety gate open
        closest_point (int): Closest labelled point to the robot's coordinates
        lid_open (int): Dewar lid open status
        lid_closed (int): Dewar lid closed status
        lid_command (int): Value of lid open command
        gripper_open (int): Gripper open status
        gripper_closed (int): Gripper closed status
        gripper_command (int): Value of close gripper command
        heater_hot (int): Is the robot heater hot
        heater_command (int): Value of heater on/off request
        heater_air_command (int): Value of heater air on/off request
        ln2_level (int): Is the LN2 high flag set
        pins_mounted (int): Number of pins mounted
        pins_lost (int): Number of pins lost
        dumbbell_state (codes.DumbbellState): Status of the dumbbell
        last_toolset_calibration (str): Timestamp of last toolset calibration
        last_left_calibration (str): Timestamp of last left position calibration
        last_middle_calibration (str): Timestamp of last middle position calibration
        last_right_calibration (str): Timestamp of last right position calibration
        last_goniometer_calibration (str): Timestamp of last goni calibration
        picker_sample (str): Sample on picker
        placer_sample (str): Sample on placer
        cavity_sample (str): Sample in cavity
        goniometer_sample (str): Sample on goniometer
        holder_types (dict):
            * keys (str): `'left'`, `'middle'`, `'right'`
            * values (codes.HolderType): Type of sample holder in position
        height_errors (dict):
            * keys (str): `'left'`, `'middle'`, `'right'`
            * values (float): height error of cassette
        puck_states (dict):
            * keys (str): `'left'`, `'middle'`, `'right'`
            * values (dict): Dict of puck names (eg `'A'`) to `codes.PuckState`\ s
        port_states (dict):
            * keys (str): `'left'`, `'middle'`, `'right'`
            * values (list): 96 element list of `codes.PortState` values
        port_distance (dict):
            * keys (str): `'left'`, `'middle'`, `'right'`
            * values (list): 96 element list of `float` values
        sample_locations (dict):
            * keys (str): `'cavity'`, `'picker`', `'placer'`, `'goniometer'`
            * values (list): `[position, port_index]` of sample at location
        mount_message (str): Mount progress message

    """
    def probe(self, ports, callback=None):
        """Probe the sample holder ports.

        Args:
            ports: Dictionary with keys: 'left', 'middle', 'right' and values
                that are 98 element lists of 1s and 0s
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('probe', ports=ports, callback=callback)

    def set_gripper(self, value, callback=None):
        """Set gripper close state.

        Args:
            value: 0 or 1
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_gripper', value=value, callback=callback)

    def set_lid(self, value, callback=None):
        """Set lid open state.

        Args:
            value: 0 or 1
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_lid', value=value, callback=callback)

    def set_heater(self, value, callback=None):
        """Set heater on or off.

        Args:
            value (int): 1 for on, 0 for off
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_heater', value=value, callback=callback)

    def set_heater_air(self, value, callback=None):
        """Set heater air on or off.

        Args:
            value (int): 1 for on, 0 for off
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_heater_air', value=value, callback=callback)

    def calibrate_toolset(self, include_find_magnet=True, quick_mode=False,
                          callback=None):
        """Calibrate the toolset

        Args:
            include_find_magnet (bool): include find magnet step
            quick_mode (bool): ???
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('calibrate_toolset',
                                  include_find_magnet=include_find_magnet,
                                  quick_mode=quick_mode,
                                  callback=callback)

    def calibrate_cassettes(self, positions, initial, callback=None):
        """Calibrate the cassette positions

        Args:
            positions (list[Position]): positions to calibrate
            initial (bool): start from top of cassettes
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('calibrate_cassettes',
                                  positions=[p.value for p in positions],
                                  initial=initial, callback=callback)

    def calibrate_goniometer(self, initial, callback=None):
        """Calibrate the goniometer

        Args:
            initial (bool): start from goniometer
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('calibrate_goniometer',
                                  initial=initial, callback=callback)

    def reset_holders(self, positions, callback=None):
        """Clear the holder type and port information for the given dewar positions.

        Args:
            positions: list of dewar positions: 'left', 'middle', 'right'
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('reset_holders', positions=positions,
                                  callback=callback)

    def reset_ports(self, ports, callback=None):
        """Clear the probe data for specific ports.

        Args:
            ports: dictionary with keys: 'left', 'middle', 'right' and values
                the ports to reset in each position
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('reset_ports', ports=ports, callback=callback)

    def mount(self, position, column, port_num, callback=None):
        """Mount a sample.

        Args:
            position: 'left', 'middle', 'right'
            column: 'A', 'B', ..., 'L'
            port_num: 1-16
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('mount', position=position, column=column,
                                  port_num=port_num, callback=callback)

    def dismount(self, callback=None):
        """Dismount a sample.

        Args:
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('dismount', callback=callback)

    def park_robot(self, dismount, callback=None):
        """Park and dismount a sample or just park the robot.

        Args:
            dismount: A boolean flag to dismount the sample before parking the robot.
            callback: Callback function receive operation state updates. Defaults to None.

        """
        return self.run_operation("park_robot", dismount=dismount, callback=callback)

    def prefetch(self, position, column, port_num, callback=None):
        """Prefetch a sample.

        Args:
            position: 'left', 'middle', 'right'
            column: 'A', 'B', ..., 'L'
            port_num: 1-16
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('prefetch', position=position, column=column,
                                  port_num=port_num, callback=callback)

    def return_prefetch(self, callback=None):
        """Return a prefetched sample to it's port.

        Args:
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('return_prefetch', callback=callback)

    def mount_and_prefetch(self, position, column, port_num,
                           prefetch_position, prefetch_column, prefetch_port_num,
                           callback=None):
        """Mount a sample and prefetch another sample.

        Args:
            position: 'left', 'middle', 'right'
            column: 'A', 'B', ..., 'L'
            port_num: 1-16
            prefetch_position: 'left', 'middle', 'right'
            prefetch_column: 'A', 'B', ..., 'L'
            prefetch_port_num: 1-16
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('mount_and_prefetch', position=position,
                                  column=column, port_num=port_num,
                                  prefetch_position=prefetch_position,
                                  prefetch_column=prefetch_column,
                                  prefetch_port_num=prefetch_port_num,
                                  callback=callback)

    def set_port_state(self, position, column, port_num, state, callback=None):
        """Set the state of port to be unknown, error etc.

        Args:
            position: 'left', 'middle', 'right'
            column: 'A', 'B', ..., 'L'
            port_num: 1-16
            state (codes.PortState): port state integer
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_port_state', position=position,
                                  column=column, port_num=port_num, state=state,
                                  callback=callback)

    def inspected(self, callback=None):
        """Set the robot state as inspected by staff.

        Args:
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('inspected', callback=callback)
