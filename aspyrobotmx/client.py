from aspyrobot import RobotClient


class RobotClientMX(RobotClient):

    def probe(self, ports):
        return self.run_operation('probe', ports=ports)

    def set_gripper(self, value):
        return self.run_operation('set_gripper', value=value)

    def set_lid(self, value):
        return self.run_operation('set_lid', value=value)

    def calibrate(self, target, run_args):
        return self.run_operation('calibrate', target=target, run_args=run_args)

    def set_port_state(self, position, column, port, state):
        return self.run_operation('set_port_state', position=position,
                                  column=column, port=port, state=state)

    def set_holder_type(self, position, type):
        return self.run_operation('set_holder_type', position=position, type=type)

    def prepare_for_mount(self):
        return self.run_operation('prepare_for_mount')

    def mount(self, position, column, port):
        return self.run_operation('mount', position=position,
                                  column=column, port=port)

    def dismount(self, position, column, port):
        return self.run_operation('dismount', position=position,
                                  column=column, port=port)
