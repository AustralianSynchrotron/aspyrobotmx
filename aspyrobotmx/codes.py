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
    need_clear = 0x00000001
    need_reset = 0x00000002
    need_cal_magnet = 0x00000004
    need_cal_cassette = 0x00000008
    need_cal_gonio = 0x00000010
    reason_lid_jam = 0x00001000
    reason_gripper_jam = 0x00002000
    reason_tolerance = 0x00020000
    reason_heater_fail = 0x00080000
    reason_abort = 0x02000000
