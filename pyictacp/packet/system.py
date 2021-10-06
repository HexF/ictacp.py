from __future__ import annotations
from abc import ABC, abstractclassmethod, abstractmethod
from pyictacp.notbuiltintypes import ByteOrder, NACKErrorCode
from pyictacp.packet import Packet

class SystemPacket(Packet, ABC, packet_type=0xC0):
    def __init_subclass__(cls) -> None:
        pass

    @classmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder) -> SystemPacket:
        if data[0] == 0xFF and data[1] == 0x00:
            return ACKPacket()
        elif data[0] == 0xFF and data[1] == 0xFF:
            return NACKPacket(
                NACKErrorCode(int.from_bytes(data[2:4], byteorder))
            )
        raise ValueError("Unknown packet type")

    def _to_bytes(self, byteorder: ByteOrder) -> bytes:
        if isinstance(self, ACKPacket):
            return bytes([0xFF, 0x00])
        elif isinstance(self, NACKPacket):
            return bytes([
                0xFF, 0xFF, #NACK
            ]) + self.error_code.value.to_bytes(2, byteorder)


class ACKPacket(SystemPacket):
    pass

class NACKPacket(SystemPacket):
    def __init__(self, error_code: NACKErrorCode) -> None:
        self.error_code = error_code