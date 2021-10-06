from pyictacp.connection import Connection
from . import Record
from ..packet.data import TroubleInputStatusDataPacketData
from ..packet.command import PermanentTroubleInputBypassCommandPacket, RemoveTroubleInputBypassCommandPacket, RequestTroubleInputStatusCommandPacket, TemporaryTroubleInputBypassCommandPacket

class TroubleInput(Record,
        data_class = TroubleInputStatusDataPacketData,
        data_request_command = RequestTroubleInputStatusCommandPacket,
        data_index_match = lambda rec, id: rec.input_index == id):
    
    def __init__(self, connection: Connection, record_id: int):
        super().__init__(connection, record_id)
        self.input_state = None
        self.bypassed = None
        self.bypassed_latched = None
        self.siren_lockout = None

    def _update(self, data: TroubleInputStatusDataPacketData):
        self.input_state = data.input_state
        self.bypassed = data.bypassed
        self.bypassed_latched = data.bypassed_latched
        self.siren_lockout = data.siren_lockout

    
    def remove_bypass(self):
        self.connection.execute_command(
            RemoveTroubleInputBypassCommandPacket(self.record_id)
        )

    def bypass(self, temporary: bool=False):
        cmd_type = TemporaryTroubleInputBypassCommandPacket if temporary else PermanentTroubleInputBypassCommandPacket

        self.connection.execute_command(
            cmd_type(self.record_id)
        )
