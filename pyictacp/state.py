from enum import Enum

class DoorLockState(Enum):
    LOCKED = 0x00
    UNLOCKED_USER_ACCESS = 0x01
    UNLOCKED_SCHEDULE = 0x02
    UNLOCKED_USER_TIMED = 0x03
    UNLOCKED_LATCHED = 0x04
    UNLOCKED_REX = 0x05
    UNLOCKED_REN = 0x06
    UNLOCKED_KEYPAD = 0x07
    UNLOCKED_AREA = 0x08
    UNLOCKED_FIRE_ALARM = 0x09

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

class AreaFlags(Enum):
    ALARM_ACTIVE = 0
    SIREN_ACTIVE = 1
    ALARMS_IN_MEMORY = 2
    REMOTE_ARMED = 3
    FORCE_ARMED = 4
    INSTANT_ARMED = 5
    PARTIAL_ARMED = 6

class OutputState(Enum):
    OFF = 0x00
    ON = 0x01
    PULSED = 0x02
    TIMED = 0x03
    PULED_TIMED = 0x04

class InputState(Enum):
    CLOSED = 0x00
    OPEN = 0x01
    SHORT = 0x02
    TAMPER = 0x03

class InputFlags(Enum):
    BYPASSED = 0
    BYPASSED_LATCHED = 1
    SIREN_LOCKOUT = 3
