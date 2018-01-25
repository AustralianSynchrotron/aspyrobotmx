from enum import IntEnum


class CassettePosition(IntEnum):
    unknown = -1
    left = 0
    middle = 1
    right = 2


class HolderType(IntEnum):
    # Warning: names must match SPEL update cassette_type messages
    unknown = 0  # unknown / absent / error
    calibration = 1
    normal = 2
    superpuck = 3


class Toolset(IntEnum):
    universal = 0
    picker = 1
    placer = 2
    twist = 3
    port_jam_recheck = 4


class PortState(IntEnum):
    full = -1
    unknown = 0
    empty = 1
    error = 2


class ProbeSpeed(IntEnum):
    probe = 0
    inside_ln2 = 1
    outside_ln2 = 2
    superslow = 3
    dance = 4
    sample_on_tong = 5


class DumbbellState(IntEnum):
    unknown = 0
    in_cradle = 1
    in_gripper = 2
    missing = 3


class PuckState(IntEnum):
    full = -1
    unknown = 0
    empty = 1
    error = 2


class RobotStatus(IntEnum):
    need_all = 0x0000007f
    need_cal_all = 0x0000003C
    need_clear = 0x00000001
    need_reset = 0x00000002
    need_cal_magnet = 0x00000004
    need_cal_cassette = 0x00000008
    need_cal_gonio = 0x00000010
    need_cal_basic = 0x00000020
    need_user_action = 0x00000040
    reason_all = 0x0fffff80
    reason_port_jam = 0x00000080
    reason_estop = 0x00000100
    reason_safeguard = 0x00000200
    reason_not_home = 0x00000400
    reason_cmd_error = 0x00000800
    reason_lid_jam = 0x00001000
    reason_gripper_jam = 0x00002000
    reason_lost_magnet = 0x00004000
    reason_collision = 0x00008000
    reason_init = 0x00010000
    reason_tolerance = 0x00020000
    reason_ln2level = 0x00040000
    reason_heater_fail = 0x00080000
    reason_cassette = 0x00100000
    reason_pin_lost = 0x00200000
    reason_wrong_state = 0x00400000
    reason_bad_arg = 0x00800000
    reason_sample_in_port = 0x01000000
    reason_abort = 0x02000000
    reason_unreachable = 0x04000000
    reason_external = 0x08000000
    in_all = 0xf0000000
    in_reset = 0x10000000
    in_calibration = 0x20000000
    in_tool = 0x40000000
    in_manual = 0x80000000
