
from pyictacp.connection import Connection
from pyictacp.record import Record
from pyictacp.packet.data import DoorStatusDataPacketData
from pyictacp.packet.command import RequestDoorStatusCommandPacket, LockDoorCommandPacket, UnlockDoorCommandPacket, UnlockDoorLatchedCommandPacket



class Door(Record,
        data_class=DoorStatusDataPacketData,
        data_request_command=RequestDoorStatusCommandPacket,
        data_index_match=lambda rec, id: rec.door_imdex == id
        ):

    def __init__(self, connection: Connection, record_id: int):
        super().__init__(connection, record_id)
        self.lock_state = None
        self.door_state = None

    def lock(self):
        self.connection.execute_command(
            LockDoorCommandPacket(
                self.record_id
            )
        )

    def unlock(self, latched:bool = False):
        cmd_type = UnlockDoorLatchedCommandPacket if latched else UnlockDoorCommandPacket

        self.connection.execute_command(
            cmd_type(
                self.record_id
            )
        )
    
    
    def _update(self, data: DoorStatusDataPacketData):
        assert data.door_index == self.record_id
        self.lock_state = data.door_lock_state
        self.door_state = data.door_state
