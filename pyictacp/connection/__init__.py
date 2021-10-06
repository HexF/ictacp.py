from __future__ import annotations
from abc import ABC, abstractmethod
from pyictacp.notbuiltintypes import ByteOrder
from pyictacp.checksum import Checksum
from pyictacp.encryption import Encryption
from typing import List
from pyictacp.packet.data import DataPacketData
from pyictacp.packet.command import CommandPacket

class Connection(ABC):
    def __init__(self, encryption: Encryption|None=None, checksum: Checksum|None=None, byteorder: ByteOrder='little') -> None:
        self.encryption = encryption
        self.checksum = checksum
        self.byteorder = byteorder
        
    @abstractmethod
    def execute_command(self, command: CommandPacket) -> List[DataPacketData] | None:
        pass
