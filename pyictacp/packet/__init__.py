from __future__ import annotations
from abc import ABC, abstractclassmethod, abstractmethod
from ..util import all_subclasses
from ..encryption import Encryption
from ..checksum import Checksum
from ..notbuiltintypes import ByteOrder

import logging
logger = logging.getLogger(__name__)

class Packet(ABC):
    HEADER_BINARY = bytes([
        0x49, 0x43
    ])

    HEADER_ASCII = bytes([
        0x49, 0x40
    ])

    PACKET_LENGTH_BYTES=2

    packet_type = -1

    def __init_subclass__(cls, packet_type: int) -> None:
        logger.debug(f"Registering packet type {packet_type:0{2}X} to {cls}")
        cls.packet_type = packet_type

    def to_bytes(self, byteorder: ByteOrder='little', ascii_mode: bool=False, encryption: Encryption|None=None, checksum:Checksum|None=None) -> bytes:
        """Packs the packet into its byte represenation
        """

        format_byte = 0
        encrypted_data = self._to_bytes()

        if encryption is not None:
            format_byte |= encryption.__class__.encryption_type & 3
            encrypted_data = encryption.encrypt(encrypted_data)

        checksum_length = checksum.__class__.length if checksum is not None else 0

        packet_length = sum([
            len(Packet.HEADER_BINARY ),
            Packet.PACKET_LENGTH_BYTES,
            2, # Packet Type & Format Byte
            len(encrypted_data),
            checksum_length
        ])

        checksum_value = bytes([])

        if checksum is not None:
            checksum_value = checksum.calculate(
                Packet.HEADER_BINARY  +
                packet_length.to_bytes(Packet.PACKET_LENGTH_BYTES, byteorder) +
                bytes([
                    self.__class__.packet_type,
                    format_byte
                ]) + 
                encrypted_data
            )

        message_body = (
            packet_length.to_bytes(Packet.PACKET_LENGTH_BYTES, byteorder) +
            bytes([
                self.__class__.packet_type,
                format_byte
            ]) + 
            encrypted_data +
            checksum_value
        )
        
        if ascii_mode:
            message_body = message_body.hex().upper().encode("ascii")

        return (Packet.HEADER_ASCII if ascii_mode else Packet.HEADER_BINARY) + message_body


    @classmethod
    def from_bytes(cls, data: bytes, byteorder: ByteOrder='little', encryption: Encryption|None=None, checksum: Checksum|None=None) -> Packet:
        """Constructs a packet from the given packet
        """
        # Validates header, checksum, length, decrypts then passes data to subclass

        # If in ASCII mode, first convert to binary-type
        logger.debug(f"Constructing packet from bytes: {data}")

        if data[:len(Packet.HEADER_ASCII)] == Packet.HEADER_ASCII:
            logger.debug("ASCII packet found, converting to binary")
            data = Packet.HEADER_BINARY + bytes.fromhex(data[len(Packet.HEADER_ASCII):].decode("ascii"))

        if data[:len(Packet.HEADER_BINARY)] != Packet.HEADER_BINARY:
            raise ValueError(f"Invalid packet header. got: '{data[:len(Packet.HEADER_BINARY)]}', want: {Packet.HEADER_BINARY}")

        logger.debug(f"Found header")
        checksum_length = 0

        if checksum is not None:
            checksum_length = checksum.__class__.length

            actual_checksum_value = data[-checksum_length:]
            checksum_value = checksum.calculate(data[:-checksum_length]) 

            if actual_checksum_value != checksum_value:
                raise ValueError(f"Invalid checksum {checksum}. got: {checksum_value}, want: {actual_checksum_value}")

            logger.debug(f"Found and validated checksum as {checksum_value}")

        packet_length = int.from_bytes(data[len(Packet.HEADER_BINARY):len(Packet.HEADER_BINARY)+Packet.PACKET_LENGTH_BYTES], byteorder)

        if packet_length != len(data):
            raise ValueError(f"Invalid packet length. got: {len(data)}, want: {packet_length}")

        packet_type = data[len(Packet.HEADER_BINARY)+Packet.PACKET_LENGTH_BYTES]
        format_byte = data[len(Packet.HEADER_BINARY)+Packet.PACKET_LENGTH_BYTES+1]

        logger.debug(f"Packet type: {packet_type:0{2}X}, Format: {format_byte:0{2}X}")

        if (format_byte & 4) > 0:
            raise ValueError("Addressed packets are not supported")

        encryption_type = format_byte & 3
        given_encryption_type = encryption.__class__.encryption_type if encryption is not None else 0

        if encryption_type != given_encryption_type:
            raise ValueError(f"Passed encryption type differs from that within packet. got: {given_encryption_type}, want: {encryption_type}")

        decrypted_data = data[len(Packet.HEADER_BINARY)+Packet.PACKET_LENGTH_BYTES+2:]

        if checksum_length > 0:
            decrypted_data = decrypted_data[:-checksum_length]

        if encryption is not None:
            decrypted_data = encryption.decrypt(decrypted_data)
            logger.debug(f"Decrypted packet")
        
        for scls in all_subclasses(cls):
            if scls.packet_type == packet_type:
                logger.debug(f"Found matching packet type: {scls}")
                return scls._from_bytes(decrypted_data, byteorder)

        raise ValueError(f"Packet type '{packet_type}' was unknown")

        

    @abstractmethod
    def _to_bytes(self, byteorder: ByteOrder='little') -> bytes:
        pass

    @abstractclassmethod
    def _from_bytes(cls, data: bytes, byteorder: ByteOrder = 'little') -> Packet:
        pass


# Import so the classes are registered
# Has to be done at bottom so Packet is constructed
import pyictacp.packet.data
import pyictacp.packet.system
import pyictacp.packet.command
