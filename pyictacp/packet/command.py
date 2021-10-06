from __future__ import annotations
from abc import ABC, abstractclassmethod, abstractmethod
from ..util import all_subclasses
from ..notbuiltintypes import ByteOrder, RecordType
from ..packet import Packet

import logging
logger = logging.getLogger(__name__)

class CommandPacket(Packet, ABC, packet_type=0x00):
    command_group = -1
    sub_command = -1

    def __init_subclass__(cls, command_group: int=None, sub_command: int=None) -> None:
        logging.debug(f"Registed command {cls} with id {command_group:0{2}X}:{sub_command:0{2}X}")
        cls.command_group = command_group
        cls.sub_command = sub_command

    def _to_bytes(self, byteorder: ByteOrder='little') -> bytes:
        return bytes([
            self.__class__.command_group,
            self.__class__.sub_command
        ]) + self._to_bytes_()

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder='little') -> CommandPacket:
        command_group = data[0]
        sub_command = data[1]

        payload = data[2:]
        for scls in all_subclasses(cls):
            if scls.command_group == command_group and scls.sub_command == sub_command:
                return scls._from_bytes_(payload, byteorder)

        raise ValueError(f"Command {command_group:X}:{sub_command:X} is unknown")
    
    def _to_bytes_(self, byteorder: ByteOrder='little') -> bytes:
        return bytes([])
    
    @classmethod
    def _from_bytes_(cls, data: bytes, byteorder: ByteOrder='little') -> CommandPacket:
        return cls()

class RecordCommandPacket(CommandPacket, command_group=-1, sub_command=-1):
    def __init__(self, record_id: int):
        self.record_id = record_id

    def _to_bytes_(self, byteorder: ByteOrder='little') -> bytes:
        return self.record_id.to_bytes(4, byteorder)

    @classmethod
    def _from_bytes_(cls, data: bytes, byteorder: ByteOrder='little') -> RecordCommandPacket:
        return cls(
            record_id = int.from_bytes(data[:4], byteorder)
        )


class PollCommandPacket(CommandPacket, command_group=0x00, sub_command=0x00):
    pass

class PanelDescriptionCommandPacket(CommandPacket, command_group=0x00, sub_command=0x01):
    pass

class LoginCommandPacket(CommandPacket, command_group=0x00, sub_command=0x02):
    MAX_PIN_LENGTH = 6

    def __init__(self, pin_number):
        self.pin_number = pin_number

        if len(pin_number) > LoginCommandPacket.MAX_PIN_LENGTH:
            raise ValueError("Provided pin has too many digits")

    def _to_bytes_(self, byteorder: ByteOrder='little') -> bytes:
        pin_digits = map(int, self.pin_number)
        pin_bytes = bytes(pin_digits)

        logger.debug(f"Login pin, pin: {self.pin_number} digits: {[*pin_digits]}")
        

        terminator = bytes([])

        if len(pin_bytes) < LoginCommandPacket.MAX_PIN_LENGTH:
            terminator = bytes([255])

        return pin_bytes + terminator

    @classmethod
    def _from_bytes_(cls, data: bytes, byteorder: ByteOrder='little') -> LoginCommandPacket:
        pin = data[:LoginCommandPacket.MAX_PIN_LENGTH]

        if pin[-1] not in [
            0x0F, # Shift In
            0x18, # Cancel
            0x0D, # Carriage return
            ] + range(10):
            # This is a terminator
            pin = pin[:-1]

        pin_digits = map(str, pin)

        return cls(
            pin_digits
        )

class LogoutCommandPacket(CommandPacket, command_group=0x00, sub_command=0x03):
    pass

class InactivityTimeCommandPacket(CommandPacket, command_group=0x00, sub_command=0x04):
    def __init__(self, inactivity_seconds: int):
        self.inactivity_time = inactivity_seconds
        if inactivity_seconds > 6000: # 100 minutes is max
            raise ValueError("Maximum inactivity time is 100 minutes")
    
    def _to_bytes_(self, byteorder: ByteOrder='little') -> bytes:
        return self.inactivity_time.to_bytes(2, byteorder)

    @classmethod
    def _from_bytes_(cls, data: bytes, byteorder: ByteOrder='little') -> InactivityTimeCommandPacket:
        return cls(
            int.from_bytes(data[:2], byteorder)
        )

class MonitorCommandPacket(CommandPacket, command_group=0x00, sub_command=0x05):
    def __init__(self, record_type: RecordType, record_id: int, start_monitoring:bool = True, force_update: bool = False):
        self.record_type = record_type
        self.record_id = record_id
        self.start_monitoring = start_monitoring
        self.force_update = force_update

        if start_monitoring and record_type is RecordType.ALL:
            raise ValueError("Cannot monitor ALL records")
        
        if not start_monitoring and force_update:
            raise ValueError("Cannot force-update when stopping monitoring")

    def _to_bytes_(self, byteorder: ByteOrder='little') -> bytes:
        flags = 0
        if self.start_monitoring:
            flags |= 1
        if self.force_update:
            flags |= 2

        return (
            self.record_type.value.to_bytes(2, byteorder) + 
            self.record_id.to_bytes(4, byteorder) +
            bytes([flags, 0]),
        )
    
    @classmethod
    def _from_bytes_(cls, data: bytes, byteorder: ByteOrder='little') -> MonitorCommandPacket:
        return cls(
            RecordType(int.from_bytes(data[2:], byteorder)),
            int.from_bytes(data[2:6], byteorder),
            data[6]&1 > 0,
            data[6]&2 > 0
        )


class EventsCommandPacket(CommandPacket, command_group=0x00, sub_command=0x06):
    def __init__(self, start_events=True, numerical_form=True, send_immediately=True):       
        self.start_events = start_events
        self.numerial_form = numerical_form
        self.send_immediately = send_immediately

    def _to_bytes_(self, byteorder: ByteOrder='little') -> bytes:
        return bytes([
            1 if self.start_events else 0,
            (
                0 if self.numerial_form else 1 |
                0 if self.send_immediately else 2
            )
        ])
    
    @classmethod
    def _from_bytes_(cls, data: bytes, byteorder: ByteOrder='little') -> EventsCommandPacket:
        return cls(
            data[0] == 1,
            data[1]&1 > 0,
            data[1]&2 > 0
        )
        

# 0x00 0x07 - ACK Configuration, ignored as changes protocol
class LockDoorCommandPacket(RecordCommandPacket, command_group=0x01, sub_command=0x00):
    pass

class UnlockDoorCommandPacket(RecordCommandPacket, command_group=0x01, sub_command=0x01):
    pass

class UnlockDoorLatchedCommandPacket(RecordCommandPacket, command_group=0x01, sub_command=0x02):
    pass

class RequestDoorStatusCommandPacket(RecordCommandPacket, command_group=0x01, sub_command=0x80):
    pass

class DisarmAreaCommandPacket(RecordCommandPacket, command_group=0x02, sub_command=0x00):
    pass

class Disarm24AreaCommandPacket(RecordCommandPacket, command_group=0x02, sub_command=0x01):
    pass

class DisarmAllAreaCommandPacket(RecordCommandPacket, command_group=0x02, sub_command=0x02):
    pass

class ArmAreaCommandPacket(RecordCommandPacket, command_group=0x02, sub_command=0x03):
    pass

class ForceArmAreaCommandPacket(RecordCommandPacket, command_group=0x02, sub_command=0x04):
    pass

class StayArmAreaCommandPacket(RecordCommandPacket, command_group=0x02, sub_command=0x05):
    pass

class InstantArmAreaCommandPacket(RecordCommandPacket, command_group=0x02, sub_command=0x06):
    pass

class RequestAreaStatusCommandPacket(RecordCommandPacket, command_group=0x02, sub_command=0x80):
    pass

class OutputOffCommandPacket(RecordCommandPacket, command_group=0x03, sub_command=0x00):
    pass

class OutputOnCommandPacket(RecordCommandPacket, command_group=0x03, sub_command=0x01):
    pass

class OutputOnTimedCommandPacket(RecordCommandPacket, command_group=0x03, sub_command=0x02):
    def __init__(self, record_id: int, on_time_seconds: int):
        super().__init__(record_id)
        self.on_time = on_time_seconds
    
    def _to_bytes_(self, byteorder: ByteOrder='little') -> bytes:
        return super()._to_bytes_(byteorder) + self.on_time.to_bytes(2, byteorder)
    
    def _from_bytes_(cls, data: bytes, byteorder: ByteOrder='little') -> OutputOnTimedCommandPacket:
        return cls(
            int.from_bytes(data[:4], byteorder),
            int.from_bytes(data[2:6], byteorder),
        )


class RequestOutputStatusCommandPacket(RecordCommandPacket, command_group=0x03, sub_command=0x80):
    pass

class RemoveInputBypassCommandPacket(RecordCommandPacket, command_group=0x04, sub_command=0x00):
    pass

class TemporaryInputBypassCommandPacket(RecordCommandPacket, command_group=0x04, sub_command=0x01):
    pass

class PermanentInputBypassCommandPacket(RecordCommandPacket, command_group=0x04, sub_command=0x02):
    pass

class RequestInputStatusCommandPacket(RecordCommandPacket, command_group=0x04, sub_command=0x80):
    pass

class SetVariableCommandPacket(RecordCommandPacket, command_group=0x05, sub_command=0x00):
    def __init__(self, record_id: int, new_value: int):
        super().__init__(record_id)
        self.new_value = new_value

    def _to_bytes_(self, byteorder: ByteOrder='little') -> bytes:
        return super()._to_bytes_() + self.new_value.to_bytes(2, byteorder)

    def _from_bytes_(cls, data: bytes, byteorder: ByteOrder) -> SetVariableCommandPacket:
        return cls(
            int.from_bytes(data[:4], byteorder),
            int.from_bytes(data[2:6], byteorder),
        )


class GetVariableCommandPacket(RecordCommandPacket, command_group=0x04, sub_command=0x80):
    pass

class RemoveTroubleInputBypassCommandPacket(RecordCommandPacket, command_group=0x06, sub_command=0x00):
    pass

class TemporaryTroubleInputBypassCommandPacket(RecordCommandPacket, command_group=0x06, sub_command=0x01):
    pass

class PermanentTroubleInputBypassCommandPacket(RecordCommandPacket, command_group=0x06, sub_command=0x02):
    pass

class RequestTroubleInputStatusCommandPacket(RecordCommandPacket, command_group=0x06, sub_command=0x80):
    pass


if __name__ == "__main__":
    pkt_bytes = bytes([
        0x49, 0x43, # Header
        0x0C, 0x00, # Length
        0x00,       # Command packet 
        0x00,       # No encryption
        0x01, 0x01, # Unlock door command
        0x07, 0x00, 0x00, 0x00 # index 7
    ])
    pkt = Packet.from_bytes(pkt_bytes)
    
    print(pkt)

    assert pkt.to_bytes() == pkt_bytes