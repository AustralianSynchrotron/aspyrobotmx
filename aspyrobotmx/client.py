from aspyrobot import RobotClient


class RobotClientMX(RobotClient):

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

    def calibrate(self, target, run_args, callback=None):
        """
        Calibrate the robot points.

        Args:
            target: 'toolset', 'cassette' or 'goniometer'
            run_args: Arguments for the calibration function
            callback: Callback function to receive operation state updates

        """
        return self.run_operation('calibrate', target=target, run_args=run_args,
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
