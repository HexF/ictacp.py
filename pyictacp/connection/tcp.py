from __future__ import annotations
from pyictacp.checksum import Checksum
from pyictacp.typez import ByteOrder, NACKErrorCode
from pyictacp.packet.system import ACKPacket, NACKPacket
from typing import List
from pyictacp.packet.data import DataPacket, DataPacketData
from pyictacp.packet.command import CommandPacket
from pyictacp.packet import Packet
import socket
from pyictacp.encryption import Encryption
from pyictacp.connection import Connection

import logging
logger = logging.getLogger(__name__)

class TCPConnection(Connection):
    def __init__(self, host: str, port: int, encryption: Encryption|None=None, checksum: Checksum|None=None, byteorder: ByteOrder='little'):
        super().__init__(encryption=encryption, checksum=checksum, byteorder=byteorder)
        self.socket_addr = (host, port)
        self.socket = None


    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(self.socket_addr)

    def close(self):
        self.socket.close()
        self.socket = None

    def _send(self, packet: bytes):
        self.socket.send(packet)

    def _recv(self) -> bytes:
        buf = bytearray()

        while True:
            if len(buf) < len(Packet.HEADER_BINARY):
                buf.extend(self.socket.recv(1))
            else:
                # We have enough bytes for the header, now check it
                is_valid = True
                for i, char in enumerate(Packet.HEADER_BINARY):
                    is_valid = is_valid and (char == buf[i])
                
                if is_valid:
                    # We found our header, now lets go to the length loop.
                    break
                buf = buf[1:] # Just cut the first byte off and try again

        length_bytes = self.socket.recv(2)
        buf.extend(length_bytes)
        expected_length = int.from_bytes(
            length_bytes,
            self.byteorder
        )

        while len(buf) != expected_length:
            # We have to do this to ensure we get the right length, and not less.
            buf.extend(self.socket.recv(1)) 

        
        return bytes(buf)


    def execute_command(self, command: CommandPacket) -> List[DataPacketData] | None:
        logger.debug(f"Transmitting packet: {command}")
        command_bytes = command.to_bytes(self.byteorder, False, self.encryption, self.checksum)
        
        logger.debug(f"Writing bytes: {command_bytes}")
        self._send(command_bytes)

        response_bytes = self._recv()
        logger.debug(f"Got bytes: {response_bytes}")
        response = Packet.from_bytes(response_bytes, self.byteorder, self.encryption, self.checksum)
        logger.debug(f"Recieving packet: {response}")


        if isinstance(response, ACKPacket):
            # No data, but we ACK'd fine
            return None 
        elif isinstance(response, NACKPacket):
            # We got a NACK, lets raise an error for this

            # First, check if its just because we aren't logged in
            # If our local state says we are, we probably timed out and can reauthenticate and try again
            if response.error_code == NACKErrorCode.USER_LOGOUT and self.logged_in:
                self.login(self.pin)
                return self.execute_command(command)

            raise ValueError(f"NACK packet: {response.error_code}") #TODO: Refactor errors
        elif issubclass(type(response), DataPacket):
            return response.data_components
        else:
            raise ValueError(f"Got type {type(response)} which is unhandled")

