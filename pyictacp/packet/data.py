from __future__ import annotations
from abc import ABC, abstractclassmethod, abstractmethod
from pyictacp.util import all_subclasses
from pyictacp.packet import Packet
from typing import List, Literal
from pyictacp.typez import AreaState, AreaTamperState, ByteOrder, DoorLockState, DoorState, FirmwareType, InputState, OutputState

import logging
logger = logging.getLogger(__name__)

class DataPacket(Packet, packet_type=0x01):
    def __init__(self, data_components: List[DataPacketData]):
        self.data_components = data_components
    
    def _to_bytes(self, byteorder: ByteOrder) -> bytes:
        data = bytearray()

        for component in self.data_components:
            if not isinstance(component, TerminatorDataPacketData):
                data.extend(component.to_bytes(bytearray))
        
        data.extend(
            TerminatorDataPacketData().to_bytes()
        )
        
        return bytes(data)

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder) -> DataPacket:
        components = []
        logger.debug(f"Constructing data packet from bytes {data}")

        while len(data) > 0:
            data_len = data[2]
            logger.debug(f"Found data type of length {data_len}")

            components.append(DataPacketData.from_bytes(
                data=data[:3+data_len],
                byteorder=byteorder
            ))
            
            data = data[3+data_len:]

        return cls(
            components
        )

        


class DataPacketData(ABC):
    data_type = -1
    def __init_subclass__(cls, data_type:int, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        logger.debug(f"Registed data type {data_type:0{4}X} to {cls}")
        cls.data_type = data_type


    @abstractmethod
    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        """Given the current packet, generate the payload porition
        """
        pass
    
    @abstractclassmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> DataPacketData:
        """Takes the payload part of data, and creates a new instance
        """
        pass

    @classmethod
    def from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> DataPacketData:
        """Takes the current packet, including data datatype and length, and creates a new DataPacketData
        """
        data_type = int.from_bytes(data[0:2], byteorder)
        data_length = data[2]
        data_payload = data[3:]

        assert data_length == len(data_payload)

        for scls in all_subclasses(cls):
            if scls.data_type == data_type:
                return scls._from_bytes(
                    data_payload,
                    byteorder
                );

        raise ValueError(
            f"Data Type {data_type:0{4}X} is unkownown" 
        )

    def to_bytes(self, byteorder: ByteOrder='little') -> bytes:
        """Given the current packet, convert it to the data portion of a data packet
        """
        payload = self._to_bytes(byteorder)
        data_type = self.__class__.data_type
        return (
            data_type.to_bytes(2, byteorder) +
            bytes([len(payload)]) + 
            payload
        )






class PanelSerialNumberDataPacketData(DataPacketData, data_type=0x0000):
    def __init__(self, serial_number: int) -> None:
        self.serial_number = serial_number
        
    
    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return self.serial_number.to_bytes(4, byteorder)

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> PanelSerialNumberDataPacketData:
        return cls(
            int.from_bytes(data[:4], byteorder)
        )


class PanelHardwareVersionDataPacketData(DataPacketData, data_type=0x0001):
    def __init__(self, hardware_version: int) -> None:
        self.hardware_version = hardware_version

    
    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return self.hardware_version.to_bytes(1, byteorder)

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> PanelHardwareVersionDataPacketData:
        return cls(
            data[0]
        )

class FirmwareTypeDataPacketData(DataPacketData, data_type=0x0002):
    def __init__(self, firmware_type: FirmwareType) -> None:
        self.firmware_type = firmware_type
    
    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return self.firmware_type.encode("ASCII")

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> FirmwareTypeDataPacketData:
        return cls(
            data[:2].decode("ASCII")
        )

class FirmwareVersionDataPacketData(DataPacketData, data_type=0x0003):
    def __init__(self, firmware_version: int) -> None:
        self.firmware_version = firmware_version

    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return self.firmware_version.to_bytes(2, byteorder)
    
    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> FirmwareVersionDataPacketData:
        return cls(
            int.from_bytes(data[:2], byteorder)
        )

class FirmwareBuildDataPacketData(DataPacketData, data_type=0x0004):
    def __init__(self, firmware_build: int) -> None:
        self.firmware_build = firmware_build

    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return self.firmware_build.to_bytes(2, byteorder)
    
    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> FirmwareBuildDataPacketData:
        return cls(
            int.from_bytes(data[:2], byteorder)
        )        

class DoorStatusDataPacketData(DataPacketData, data_type=0x0100):
    def __init__(self, door_index: int, door_lock_state: DoorLockState, door_state: DoorState) -> None:
        self.door_index = door_index
        self.door_lock_state = door_lock_state
        self.door_state = door_state

    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return (
            self.door_index.to_bytes(4, byteorder) +
            bytes([
                self.door_lock_state.value,
                self.door_state.value,
                0,
                0
            ])
        )

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> DoorStatusDataPacketData:
        return cls(
            int.from_bytes(data[:4], byteorder),
            DoorLockState(data[4]),
            DoorState(data[5])
        )
    
class AreaStatusDataPacketData(DataPacketData, data_type=0x0200):
    def __init__(self,
                area_index: int,
                area_state: AreaState,
                area_tamper_state: AreaTamperState,
                alarm_active: bool=False,
                siren_active: bool=False,
                alarm_in_memory: bool=False,
                remote_armed: bool=False,
                instant_armed: bool=False,
                partial_armed: bool=False
                ) -> None:
        self.area_index = area_index
        self.area_state = area_state
        self.area_tamper_state = area_tamper_state
        self.alarm_active = alarm_active
        self.siren_active = siren_active
        self.alarm_in_memory = alarm_in_memory
        self.remote_armed = remote_armed
        self.instant_armed = instant_armed
        self.partial_armed = partial_armed

    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        flags = (
            (1 << 0) if self.alarm_active else 0 |
            (1 << 1) if self.siren_active else 0 |
            (1 << 2) if self.alarm_in_memory else 0 |
            (1 << 3) if self.remote_armed else 0 |
            (1 << 4) if self.instant_armed else 0 |
            (1 << 5) if self.partial_armed else 0 
        )

        return (
            self.area_index.to_bytes(4, byteorder) +
            bytes([
                self.area_state.value,
                self.area_tamper_state.value,
                flags,
                0
            ])
        )

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> AreaStatusDataPacketData:
        alarm_active, siren_active, alarm_in_memory, remote_armed, instant_armed, partial_armed = [
            (data[6] & (1<<i)) > 0
            for i in range(6)
        ]

        return cls(
            int.from_bytes(data[:4], byteorder),
            AreaState(data[4]),
            AreaTamperState(data[5]),
            alarm_active,
            siren_active,
            alarm_in_memory,
            remote_armed,
            instant_armed,
            partial_armed
        )

class OutputStatusDataPacketData(DataPacketData, data_type=0x0300):
    def __init__(self, output_index: int, output_reference: str, output_state: OutputState) -> None:
        self.output_index = output_index
        self.output_reference = output_reference
        self.output_state = output_state

    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return (
            self.output_index.to_bytes(4, byteorder) +
            self.output_reference[:8].encode("ASCII") +
            bytes([
                self.output_state.value,
                0,
                0,
                0
            ])
        )

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> OutputStatusDataPacketData:
        return cls(
            int.from_bytes(data[:4], byteorder),
            data[4:12].decode("ASCII"),
            OutputState(data[12])
        )
        
class InputStatusDataPacketData(DataPacketData, data_type=0x0400):
    def __init__(self,
        input_index: int,
        input_reference: str,
        input_state: InputState,
        bypassed: bool=False,
        bypassed_latched: bool=False,
        siren_lockout: bool=False,
        ) -> None:
        
        self.input_index = input_index
        self.input_reference = input_reference
        self.input_state = input_state
        self.bypassed = bypassed
        self.bypassed_latched = bypassed_latched
        self.siren_lockout = siren_lockout

    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        flags = (
            (1<<0) if self.bypassed else 0 |
            (1<<1) if self.bypassed_latched else 0 |
            (1<<3) if self.siren_lockout else 0
        )
        return (
            self.input_index.to_bytes(4, byteorder) +
            self.input_reference[:8].encode("ASCII") +
            bytes([
                self.input_state.value,
                flags,
                0,
                0
            ])
        )

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> InputStatusDataPacketData:
        bypassed, bypassed_latched, _, siren_lockout = [
            (data[6] & (1<<i)) > 0
            for i in range(4)
        ]
        return cls(
            int.from_bytes(data[:4], byteorder),
            data[4:12].decode("ASCII"),
            InputState(data[12]),
            bypassed,
            bypassed_latched,
            siren_lockout
        )

class VariableStatusDataPacketData(DataPacketData, data_type=0x0500):
    def __init__(self,
        variable_index: int,
        variable_value: int
    ) -> None:
        self.variable_index = variable_index
        self.variable_value = variable_value

    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return (
            self.variable_index.to_bytes(4, byteorder) +
            self.variable_value.to_bytes(2, byteorder)
        )

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> VariableStatusDataPacketData:
        return cls(
            int.from_bytes(data[:4], byteorder),
            int.from_bytes(data[4:6], byteorder)
        )


class TroubleInputStatusDataPacketData(DataPacketData, data_type=0x0600):
    def __init__(self,
        trouble_input_index: int,
        trouble_input_reference: str,
        trouble_input_state: InputState,
        bypassed: bool=False,
        bypassed_latched: bool=False
        ) -> None:
        
        self.trouble_input_index = trouble_input_index
        self.trouble_input_reference = trouble_input_reference
        self.trouble_input_state = trouble_input_state
        self.bypassed = bypassed
        self.bypassed_latched = bypassed_latched

    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        flags = (
            (1<<0) if self.bypassed else 0 |
            (1<<1) if self.bypassed_latched else 0 
        )
        return (
            self.trouble_input_index.to_bytes(4, byteorder) +
            self.trouble_input_reference[:8].encode("ASCII") +
            bytes([
                self.trouble_input_state.value,
                flags,
                0,
                0
            ])
        )

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> TroubleInputStatusDataPacketData:
        bypassed, bypassed_latched = [
            (data[6] & (1<<i)) > 0
            for i in range(2)
        ]
        return cls(
            int.from_bytes(data[:4], byteorder),
            data[4:12].decode("ASCII"),
            InputState(data[12]),
            bypassed,
            bypassed_latched
        )

class HumanReadableEventDataPacketData(DataPacketData, data_type=0x0130):
    def __init__(self, event_message: str) -> None:
        self.event_message = event_message
    
    def _to_bytes(self, byteorder: ByteOrder = 'little') -> bytes:
        return self.event_message.encode("ASCII") + bytes([0])

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> HumanReadableEventDataPacketData:
        return cls(
            data[:-1].decode("ASCII")
        )

class TerminatorDataPacketData(DataPacketData, data_type=0xFFFF):
    def _to_bytes(self, byteorder: ByteOrder) -> bytes:
        return bytes()
    
    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder) -> TerminatorDataPacketData:
        return cls()


if __name__ == "__main__":
    # Test we can resolve the bytes to a type

    org = bytes([
        0x00, 0x03,
        0x10,
        0x05, 0x00, 0x00, 0x00,
        0x43, 0x50, 0x30, 0x30, 0x31, 0x3A, 0x30, 0x35,
        0x01,
        0x00, 0x00, 0x00
    ])

    x = DataPacketData.from_bytes(org)

    print(x.output_index)
    print(x.output_reference)
    print(x.output_state)

    assert org == x.to_bytes()