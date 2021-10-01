from enum import Enum

from pyictacp.encryption import Encryption
from pyictacp.util import Checksum, calculate_checksum

HEADER_HIGH = 0x43
HEADER_LOW = 0x49

class PacketType(Enum):
    COMMAND = 0x00
    DATA = 0x01
    SYSTEM = 0xC0


class Packet:
    def __init__(self, packet_type: PacketType, encryption: Encryption, checksum: Checksum, *args):
        self.type = packet_type
        self.encryption = encryption
        self.checksum = checksum

        if packet_type is PacketType.COMMAND:
            self.command = args[0]
        elif packet_type is PacketType.SYSTEM:
            self.raw_data = args[0]
    
        


    def to_bytes(self) -> bytes:

        byte_list = bytearray()

        # Header Info
        byte_list.extend([
            HEADER_LOW,
            HEADER_HIGH,
            0,  # Length Placeholder
            0,  # Length Placeholder
            self.type.value,
            self.encryption.command_value
        ])

        if self.type == PacketType.COMMAND:
            byte_list.extend([
                self.command.record_type.value,
                self.command.command_type
            ])

            byte_list.extend(self.command._packet_data())

        if self.type == PacketType.SYSTEM:
            byte_list.extend(self.raw_data)

        encrypted_packet = self.encryption.encrypt_packet(bytes(byte_list))

        packet = bytearray(encrypted_packet)
        packet_length = len(packet) + self.checksum.value

        len_bytes = packet_length.to_bytes(2, 'little')
        packet[2] = len_bytes[0]
        packet[3] = len_bytes[1]

        packet.extend(
            calculate_checksum(packet, self.checksum)
        )

        return bytes(packet)
        
