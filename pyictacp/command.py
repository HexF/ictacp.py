from enum import Enum

from pyictacp.encryption import Encryption
from pyictacp.packet import Packet, PacketType
import pyictacp.util as util

class RecordType(Enum):
    SYSTEM = 0x00
    DOOR = 0x01
    AREA = 0x02
    OUTPUT = 0x03
    INPUT = 0x04
    VARIABLE = 0x05
    TROUBLE_INPUT = 0x06
    CONFIG = 0xF0

class Priority(Enum):
    HIGHEST = 1
    HIGH = 3
    NORMAL = 5
    LOW = 7
    LOWEST = 9
    CONTROLLER_CONFIG = -1

PIN_MAX_LENGTH = 6


class Command:
    def __init__(self, record_type, command_type, data_length, priority):
        self.record_type = record_type
        self.command_type = command_type
        self.data_length = data_length
        self.priority = priority

    def _packet_data(self):
        raise NotImplementedError("_packet_data should be implemented in child class")

    def to_packet(self, encryption: Encryption, checksum: util.Checksum):
        return Packet(PacketType.COMMAND, encryption, checksum, self)
        



class EntityCommand(Command):
    def __init__(self, record_type, command_type, data_length, priority, index: int):
        super().__init__(record_type, command_type, data_length, priority)
        self.index = index

    def _packet_data(self):
        return self.index.to_bytes(4, 'little')

class SystemPollCommand(Command):
    def __init__(self):
        super().__init__(RecordType.SYSTEM, 0x0, 0, Priority.HIGH)

    def _packet_data(self):
        return bytes(0)


class SystemDescriptionCommand(Command):
    def __init__(self):
        super().__init__(RecordType.SYSTEM, 0x01, 0, Priority.NORMAL)

    def _packet_data(self):
        return bytes(0)


class SendLoginCommand(Command):
    def __init__(self, pin: str):
        super().__init__(RecordType.SYSTEM, 0x02, 2, Priority.HIGH)
        self.pin = pin

    def _packet_data(self):
        digits = []

        for char in self.pin:
            digits.append(
                int(char)
            )

        if len(digits) < PIN_MAX_LENGTH:
            digits.append(0xFF)

        return bytes(digits)


class SendLogoutCommand(Command):
    def __init__(self):
        super().__init__(RecordType.SYSTEM, 0x03, 0, Priority.NORMAL)

    def _packet_data(self):
        return bytes(0)


class SystemLoginTimeCommand(Command):
    def __init__(self):
        super().__init__(RecordType.SYSTEM, 0x04, 2, Priority.NORMAL)


class SystemMonitorRecordCommand(Command):
    def __init__(self, record_type: RecordType, record_id: int):
        super().__init__(RecordType.SYSTEM, 0x05, 8, Priority.NORMAL)

        self.item_record_type = record_type
        self.item_record_index = record_id

    def _packet_data(self):
        return bytes([
            # Item Type
            self.item_record_type.value,
            0  
        ]) + self.item_record_index.to_bytes(4, 'little') + bytes([
            1, # Start Monitoring
            0, # End of Packet
        ])


class SystemRequestEventsCommand(Command):
    def __init__(self):
        super().__init__(RecordType.SYSTEM, 0x06, 2, Priority.NORMAL)

    def _packet_data(self):
        return bytes([
            0x01, # StartCommand Monitoring (0x00 is stop)
            0x01  # Format (bit 0 = 0-numberic, 1-human readable, bit 1 = 0-immediate, 1-after next event)
        ])


class SystemACKControlCommand(EntityCommand):
    def __init__(self, index):
        super().__init__(RecordType.SYSTEM, 0x07, 8, Priority.NORMAL)


class DoorLockCommand(EntityCommand):
    def __init__(self, door_id):
        super().__init__(RecordType.DOOR, 0x00, 4, Priority.NORMAL, door_id)


class DoorUnlockCommand(EntityCommand):
    def __init__(self, door_id):
        super().__init__(RecordType.DOOR, 0x01, 4, Priority.NORMAL, door_id)


class DoorLatchCommand(EntityCommand):
    def __init__(self, door_id):
        super().__init__(RecordType.DOOR, 0x02, 4, Priority.NORMAL, door_id)


class AreaDisarmCommand(EntityCommand):
    def __init__(self, area_id):
        super().__init__(RecordType.AREA, 0x00, 4, Priority.NORMAL, area_id)


class AreaDisarm24HRCommand(EntityCommand):
    def __init__(self, area_id):
        super().__init__(RecordType.AREA, 0x01, 4, Priority.NORMAL, area_id)


class AreaDisarmAllCommand(Command):
    def __init__(self):
        super().__init__(RecordType.AREA, 0x02, 4, Priority.NORMAL)


class AreaArmCommand(EntityCommand):
    def __init__(self, area_id):
        super().__init__(RecordType.AREA, 0x03, 4, Priority.NORMAL, area_id)


class AreaForceArmCommand(EntityCommand):
    def __init__(self, area_id):
        super().__init__(RecordType.AREA, 0x04, 4, Priority.NORMAL, area_id)


class AreaStayArmCommand(EntityCommand):
    def __init__(self, area_id):
        super().__init__(RecordType.AREA, 0x05, 4, Priority.NORMAL, area_id)


class AreaInstantArmCommand(EntityCommand):
    def __init__(self, area_id):
        super().__init__(RecordType.AREA, 0x06, 4, Priority.NORMAL, area_id)


class OutputOffCommand(EntityCommand):
    def __init__(self, output_id):
        super().__init__(RecordType.OUTPUT, 0x00, 4, Priority.NORMAL, output_id)


class OutputOnCommand(EntityCommand):
    def __init__(self, output_id):
        super().__init__(RecordType.OUTPUT, 0x01, 4, Priority.NORMAL, output_id)


class OutputOnTimedCommand(EntityCommand):
    def __init__(self, output_id, time : int):
        super().__init__(RecordType.OUTPUT, 0x02, 6, Priority.NORMAL, output_id)
        self.time = time
    
    def _packet_data(self):
        return bytes(
            super()._packet_data() + 
            self.time.to_bytes(4, 'little')
            )


class InputRemoveBypassCommand(EntityCommand):
    def __init__(self, input_id):
        super().__init__(RecordType.INPUT, 0x00, 4, Priority.NORMAL, input_id)


class InputTemporaryBypassCommand(EntityCommand):
    def __init__(self, input_id):
        super().__init__(RecordType.INPUT, 0x01, 4, Priority.NORMAL, input_id)


class InputPermanantBypassCommand(EntityCommand):
    def __init__(self, input_id):
        super().__init__(RecordType.INPUT, 0x02, 4, Priority.NORMAL, input_id)


class VariableSetCommand(EntityCommand):
    def __init__(self, variable_id, new_value):
        super().__init__(RecordType.VARIABLE, 0x00, 6, Priority.NORMAL, variable_id)
        self.new_value = new_value
    
    def _packet_data(self):
        return bytes(
            super()._packet_data() + 
            self.new_value.to_bytes(2, 'little')
            )

class VariableGetCommand(EntityCommand):
    def __init__(self, variable_id):
        super().__init__(RecordType.VARIABLE, 0x80, 6, Priority.NORMAL, variable_id)


class RequestStatusCommand(Command):
    def __init__(self):
        super().__init__(RecordType.SYSTEM, 0x80, 4, Priority.NORMAL)


class PinDigitCommand(Command):
    def __init__(self):
        super().__init__(RecordType.CONFIG, 0x00, 0, Priority.CONTROLLER_CONFIG)

    def _packet_data(self):
        return bytes(0)


class ClearLoginCommand(Command):
    def __init__(self):
        super().__init__(RecordType.CONFIG, 0x01, 0, Priority.CONTROLLER_CONFIG)

    def _packet_data(self):
        return bytes(0)


class MonitorLoginStatusCommand(Command):
    def __init__(self):
        super().__init__(RecordType.CONFIG, 0x02, 0, Priority.CONTROLLER_CONFIG)


class MonitorConnectionStatusCommand(Command):
    def __init__(self):
        super().__init__(RecordType.CONFIG, 0x03, 0, Priority.CONTROLLER_CONFIG)


class MonitorQueuedCommandsCommand(Command):
    def __init__(self):
        super().__init__(RecordType.CONFIG, 0x04, 0, Priority.CONTROLLER_CONFIG)


class MonitorPINNumberCommand(Command):
    def __init__(self):
        super().__init__(RecordType.CONFIG, 0x05, 0, Priority.CONTROLLER_CONFIG)


