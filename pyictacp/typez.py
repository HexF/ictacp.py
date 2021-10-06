from enum import Enum
from typing import Literal, TypedDict

ByteOrder = Literal['little', 'big']


class RecordType(Enum):
    ALL             = 0x0000
    DOOR            = 0x0001
    AREA            = 0x0002
    AREA_INPUT      = 0x0102
    OUTPUT          = 0x0003
    INPUT           = 0x0004
    VARIABLE        = 0x0005
    TROUBLE_INPUT   = 0x0006

class DoorLockState(Enum):
    LOCKED = 0x00
    UNLOCKED_ACCESS = 0x01
    UNLOCKED_SCHEDULE = 0x02
    UNLOCKED_TIMED = 0x03
    UNLOCKED_LATCHED = 0x04
    UNLOCKED_REX = 0x05
    UNLOCKED_REN = 0x06
    UNLOCKED_KEYPAD = 0x07
    UNLOCKED_AREA = 0x08
    UNLOCKED_FIRE = 0x09

class DoorState(Enum):
    CLOSED = 0x00
    OPEN = 0x01
    OPEN_ALERT = 0x02
    LEFT_OPEN = 0x03
    FORCED_OPEN = 0x04

class AreaState(Enum):
    DISARMED = 0x00
    INPUTS_OPEN = 0x01
    TROUBLE_CONDITION = 0x02
    BYPASS_ERROR = 0x03
    BYPASS_WARNING = 0x04
    NOT_VACANT = 0x05
    ARMED = 0x80
    EXIT_DELAY = 0x81
    ENTRY_DELAY = 0x82
    DISARM_DELAY = 0x83
    CODE_DELAY = 0x84

class AreaTamperState(Enum):
    DISARMED = 0x00
    BUSY = 0x01
    ARMED = 0x80

class OutputState(Enum):
    OFF = 0x00
    ON = 0x01
    ON_PULSED = 0x02
    ON_TIMED = 0x03
    ON_PULSED_TIMED = 0x04

class InputState(Enum):
    CLOSED = 0x00
    OPEN = 0x01
    SHORT = 0x02
    TAMPER = 0x03

class NACKErrorCode(Enum):
    SERVICE_INDEX_NOT_VALID = 0x0121
    SERVICE_COMMAND_NOT_VALID = 0x0120
    USER_LOGIN = 0x0300
    USER_LOGOUT = 0x0301
    USER_INVALID = 0x0302
    USER_AXS_AREA = 0x0303
    USER_DOOR_GROUP = 0x030A
    USER_AXS_DOOR_AXS_LVL = 0x030F
    DOOR_SVC_DENIED_LOCKDOWN = 0x0A23
    DOOR_ALREADY_IN_STATE = 0x0A32
    DOOR_INTERLOCK_ACTIVE = 0x0A12
    AREA_NO_CHANGE = 0x0869
    USER_ACCESS_RIGHTS = 0x0303
    INPUT_COMMAND_FAILED = 0x040E

FirmwareType = Literal['GX','SE','LE']

class PanelInformation(TypedDict):
    serial_number: str
    hardware_version: int
    firmware_type: FirmwareType
    firmware_version: int
    firmware_build: int