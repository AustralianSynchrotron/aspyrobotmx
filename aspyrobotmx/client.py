from aspyrobot import RobotClient


class RobotClientMX(RobotClient):
    """
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

    """
    def probe(self, ports, callback=None):
        """
        Probe the sample holder ports.

        Args:
            ports: Dictionary with keys: 'left', 'middle', 'right' and values
                that are 98 element lists of 1s and 0s
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('probe', ports=ports, callback=callback)

    def set_gripper(self, value, callback=None):
        """
        Set gripper close state.

        Args:
            value: 0 or 1
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_gripper', value=value, callback=callback)

    def set_lid(self, value, callback=None):
        """
        Set lid open state.

        Args:
            value: 0 or 1
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_lid', value=value, callback=callback)

    def set_heater(self, value, callback=None):
        """
        Set heater on or off.

        Args:
            value (int): 1 for on, 0 for off
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_heater', value=value, callback=callback)

    def set_heater_air(self, value, callback=None):
        """
        Set heater air on or off.

        Args:
            value (int): 1 for on, 0 for off
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_heater_air', value=value, callback=callback)

    def calibrate(self, target, task_args, callback=None):
        """
        Calibrate the robot points.

        Args:
            target: 'toolset', 'cassette' or 'goniometer'
            task_args: Arguments for the calibration function
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('calibrate', target=target, task_args=task_args,
                                  callback=callback)

    def reset_ports(self, ports, callback=None):
        """
        Clear the probe data for specific ports.

        Args:
            ports: dictionary with keys: 'left', 'middle', 'right' and values
                the ports to reset in each position
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('reset_ports', ports=ports, callback=callback)

    def set_holder_type(self, position, type, callback=None):
        """
        Set the holder type in a dewar position.

        Args:
            position: 'left', 'middle', 'right'
            type: 'unknown', 'calibration', 'normal', 'superpuck'
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('set_holder_type', position=position,
                                  type=type, callback=callback)

    def prepare_for_mount(self, callback=None):
        """
        Move the robot to the cooling point.

        Args:
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('prepare_for_mount', callback=callback)

    def mount(self, position, column, port, callback=None):
        """
        Mount a sample.

        Args:
            position: 'left', 'middle', 'right'
            column: 'A', 'B', ..., 'L'
            port: 1-16
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('mount', position=position, column=column,
                                  port=port, callback=callback)

    def dismount(self, position, column, port, callback=None):
        """
        Dismount a sample to the specified port.

        Args:
            position: 'left', 'middle', 'right'
            column: 'A', 'B', ..., 'L'
            port: 1-16
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('dismount', position=position, column=column,
                                  port=port, callback=callback)
