from asyncio import transports
import logging
import asyncio

from ictacp.command import Command, RecordType
import ictacp.command as cmd
from ictacp.packet import HEADER_HIGH, HEADER_LOW, Packet, PacketType
from ictacp.state import AreaFlags, AreaState, AreaTamperState, DoorLockState, DoorState, InputFlags, InputState, OutputState
from ictacp.util import Checksum, calculate_checksum
from ictacp.encryption import Encryption, NoneEncryption

logger = logging.getLogger(__name__)

NACK_ERROR_CODES = { # pg. 37
    0x0121: ("SERVICE_INDEX_NOT_VALID", "The index of the record to control was not valid."),
    0x0120: ("SERVICE_COMMAND_NOT_VALID", "The requested command was not valid."),
    0x0300: ("USER_LOGIN", "A login command was received while a user was already logged in."),
    0x0301: ("USER_LOGOUT", "A control command was received while no user was logged in."),
    0x0302: ("USER_INVALID", "A login command was received but the PIN did not match a valid user."),
    0x0303: ("USER_AXS_AREA", "The area action was denied because the user does not have any valid access levels assigned for that area."),
    0x030A: ("USER_DOOR_GROUP", "The door group was not valid or the user did not have access rights to that door group."),
    0x030F: ("USER_AXS_DOOR_AXS_LVL", "The door action was denied because the user does not have any valid access levels assigned."),
    0x0A23: ("DOOR_SVC_DENIED_LOCKDOWN", "The door action was denied because the door was in lock‐down mode."),
    0x0A32: ("DOOR_ALREADY_IN_STATE", "The door action was valid but the door did not change state because it was already in that state."),
    0x0A12: ("DOOR_INTERLOCK_ACTIVE", "The door action was denied because of an interlock on the door."),
    0x0869: ("AREA_NO_CHANGE", "The area action was valid but the area did not change state because it was already in that state."),
    0x0303: ("USER_ACCESS_RIGHTS", "The area action was denied because the user did not have sufficient arm/disarm rights."),
    0x040E: ("INPUT_COMMAND_FAILED", "The Input was unable to be bypassed either because of Input configuration or because it's in an armed area."),
}

class ACPProtocol(asyncio.Protocol):
    def __init__(self, encryption: Encryption, checksum: Checksum, state_callback):
        self.encryption = encryption
        self.checksum = checksum

        self.state_callback = state_callback

        self.serial_number = None
        self.hardware_version = None
        self.firmware_type = None
        self.firmware_version = None
        self.firmware_build = None
        self.logged_in = False

        self.door_states = {}
        self.area_states = {}
        self.output_states = {}
        self.input_states = {}
        self.variable_states = {}
        self.trouble_input_states = {}

        self.buffer = bytearray()

        self.transport = None
        self.polling_task = None

        loop = asyncio.get_running_loop()
        self.packet_ready = loop.create_future()
        self.packet_ready.set_result(None)

    async def poll_task(self):
        while True:
            await asyncio.sleep(10)
            await self.execute_command(cmd.SystemPollCommand())
            logger.log("sent poll")

    async def execute_command(self, command: Command):
        packet = command.to_packet(self.encryption, self.checksum)

        self.transport.write(packet.to_bytes())
        logger.debug("Sent %s", packet.to_bytes())        

        loop = asyncio.get_running_loop()
        self.packet_ready = loop.create_future()

        return await self.packet_ready

        





    def _process_packet(self, original_packet):
        csless_packet = original_packet
        if self.checksum != Checksum.NONE:
            checksum = csless_packet[-self.checksum.value:]
            csless_packet = csless_packet[:-self.checksum.value]
            actual_cs = calculate_checksum(csless_packet, self.checksum)

            if actual_cs != checksum:
                raise Exception(f"Recieved data was corrupted. Got checksum: {checksum}, expected: {actual_cs}")

        packet = self.encryption.decrypt_packet(csless_packet)

        if packet[:2].decode("ascii") != "IC":
            raise Exception(f"Recieved data was corrupted. Got header: {packet[:2]}, expected: IC")

        if int.from_bytes(packet[2:4], 'little') != len(original_packet):
            raise Exception(f"Recieved data was corrupted. Got length: {len(original_packet)}, expected: {int.from_bytes(packet[2:4], 'little')}")

        packet_type = PacketType(packet[4])
        
        packet_data = packet[6:]
        if packet_type == PacketType.DATA:
            self._process_data_packet(packet_data)

            if self.packet_ready.done():
                logger.debug("ACKing data packet")
                self.transport.write(Packet(PacketType.SYSTEM, self.encryption, self.checksum, bytes([255, 0])).to_bytes())
            else:
                self.packet_ready.set_result(True)



        elif packet_type == PacketType.SYSTEM:
            result = self._process_system_packet(packet_data)
            if not self.packet_ready.done():
                self.packet_ready.set_result(result)



    def _process_data_packet(self, packet: bytes):
        
        while len(packet) > 0:
            data_type = int.from_bytes(packet[:2], 'little')
            data_len = packet[2]
            data = packet[3:3+data_len]
            packet = packet[3+data_len:]


            # Skip this random data - seems to crash the handler /shrug
            if data_len > 5 and data[-2] == 0xFF:
                continue

            if data_type == 0xFFFF:
                break
            elif data_type == 0x0000:
                self.serial_number = format(int.from_bytes(data, 'little'), 'X')
            elif data_type == 0x0001:
                self.hardware_version = data[0]
            elif data_type == 0x0002:
                self.firmware_type = data.decode("ascii")
            elif data_type == 0x0003:
                self.firmware_version = int.from_bytes(data, 'little')
            elif data_type == 0x0004:
                self.firmware_build = int.from_bytes(data, 'little')        

            
            elif data_type == 0x0100:
                record_id = int.from_bytes(data[:4], 'little')
                lock_state = DoorLockState(data[4])
                state = DoorState(data[5])
                self.door_states[record_id] = (state, lock_state)

                if self.state_callback is not None:
                    self.state_callback(RecordType.DOOR, record_id, self.door_states[record_id])
            
            elif data_type == 0x0200:
                record_id = int.from_bytes(data[:4], 'little')
                state = AreaState(data[4])
                tamper_state = AreaTamperState(data[5])
                flags = []
                for i in range(8):
                    if (data[6]>>i)&1 == 1:
                        flags.append(AreaFlags(i))
                self.area_states[record_id] = (state, tamper_state, flags)

                if self.state_callback is not None:
                    self.state_callback(RecordType.AREA, record_id, self.area_states[record_id])
            
            elif data_type == 0x0300:
                record_id = int.from_bytes(data[:4], 'little')
                state = OutputState(data[12])
                self.output_states[record_id] = state

                if self.state_callback is not None:
                    self.state_callback(RecordType.OUTPUT, record_id, self.output_states[record_id])
            
            elif data_type == 0x0400:
                record_id = int.from_bytes(data[:4], 'little')
                state = InputState(data[12])
                flags = []
                for i in range(8):
                    if (data[13]>>i)&1 == 1:
                        flags.append(InputFlags(i))

                self.input_states[record_id] = (state, flags)

                if self.state_callback is not None:
                    self.state_callback(RecordType.INPUT, record_id, self.input_states[record_id])

            elif data_type == 0x0500:
                record_id = int.from_bytes(data[:4], 'little')
                state = int.from_bytes(data[4:6], 'little')
                self.variable_states[record_id] = state

                if self.state_callback is not None:
                    self.state_callback(RecordType.VARIABLE, record_id, self.variable_states[record_id])
            
            elif data_type == 0x0600:
                record_id = int.from_bytes(data[:4], 'little')
                state = InputState(data[12])
                flags = []
                for i in range(8):
                    if (data[6]>>i)&1 == 1:
                        flags.append(InputFlags(i))

                self.trouble_input_states[record_id] = (state, flags)

                if self.state_callback is not None:
                    self.state_callback(RecordType.TROUBLE_INPUT, record_id, self.trouble_input_states[record_id])
            
    def _process_system_packet(self, packet):
        if packet[0] != 0xFF:
            raise Exception(f"Invalid system command {packet}")
        
        if packet[1] == 0:
            # ACK
            logger.debug("Got ACK")
            return True
        elif packet[1] == 0xFF:
            # NACK w/ Error
            event_code = int.from_bytes(packet[2:4], 'little')
            reference, desc = NACK_ERROR_CODES[event_code]
            logger.warn("Got NACK: %s (%s): %s", reference, event_code, desc)
            return False

    # protocol handlers

    def connection_made(self, transport: transports.BaseTransport) -> None:
        self.transport = transport
        self.polling_task = asyncio.create_task(self.poll_task())

    def connection_lost(self, exc: Exception) -> None:
        self.transport = None
        self.polling_task.cancel()


    def data_received(self, data: bytes) -> None:
        self.buffer.extend(data)
        logger.debug("Raw recv: %s", data)

        while len(self.buffer) > 4:
            

            if self.buffer[0] == HEADER_LOW and self.buffer[1] == HEADER_HIGH:
                packet_length = int.from_bytes(self.buffer[2:4], 'little')
                if len(self.buffer) >= packet_length:
                    # Data is ready to process
                    packet = bytes(self.buffer[:packet_length])
                    self.buffer = self.buffer[packet_length + 1:]
                    logger.debug("Packet: %s", packet)
                    self._process_packet(packet)
                else:
                    break
            else:
                self.buffer = self.buffer[1:]

        

    # Public Methods
    async def get_system_info(self):
        if await self.execute_command(cmd.SystemDescriptionCommand()) is not True:
            return False

        return {
            "serial_number": self.serial_number,
            "hardware_version": self.hardware_version,
            "firmware_type": self.firmware_type,
            "firmware_version": self.firmware_version,
            "firmware_build": self.firmware_build
        }

    async def login(self, pin):
        if await self.execute_command(cmd.SendLoginCommand(pin)) is not True:
            return False
        
        self.logged_in = True
        return True

    async def logout(self):
        if self.logged_in:
            return await self.execute_command(cmd.SendLogoutCommand()) is True

        return True

    async def watch(self, record_type: RecordType, record_id: int):
        return await self.execute_command(cmd.SystemMonitorRecordCommand(record_type, record_id)) is True
