from aspyrobot import RobotClient


class RobotClientMX(RobotClient):

    def probe(self, ports, callback=None):
        return self.run_operation('probe', ports=ports, callback=callback)

    def set_gripper(self, value, callback=None):
        return self.run_operation('set_gripper', value=value, callback=callback)

    def set_lid(self, value, callback=None):
        return self.run_operation('set_lid', value=value, callback=callback)

    def calibrate(self, target, run_args, callback=None):
        return self.run_operation('calibrate', target=target, run_args=run_args,
                                  callback=callback)

    def reset_ports(self, ports, callback=None):
        """
        ports: dictionary with keys: 'left', 'middle', 'right' and values
            the ports to reset in each position
        """
        return self.run_operation('reset_ports', ports=ports, callback=callback)

    def set_holder_type(self, position, type, callback=None):
        return self.run_operation('set_holder_type', position=position,
                                  type=type, callback=callback)

    def prepare_for_mount(self, callback=None):
        return self.run_operation('prepare_for_mount', callback=callback)

    def mount(self, position, column, port, callback=None):
        return self.run_operation('mount', position=position,
                                  column=column, port=port, callback=callback)

    def dismount(self, position, column, port, callback=None):
        return self.run_operation('dismount', position=position,
                                  column=column, port=port, callback=callback)
