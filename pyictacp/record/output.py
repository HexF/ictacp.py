from __future__ import annotations
from pyictacp.connection import Connection
from pyictacp.record import Record
from pyictacp.packet.data import OutputStatusDataPacketData
from pyictacp.packet.command import RequestOutputStatusCommandPacket, OutputOffCommandPacket, OutputOnTimedCommandPacket, OutputOnCommandPacket
from datetime import timedelta

class Output(Record,
        data_class = OutputStatusDataPacketData,
        data_request_command = RequestOutputStatusCommandPacket,
        data_index_match=lambda rec, id: rec.output_index == id):

    def __init__(self, connection: Connection, record_id: int):
        super().__init__(connection, record_id)
        self.output_state = None

    def _update(self, data: OutputStatusDataPacketData):
        assert data.output_index == self.record_id
        self.output_state = data.output_state
    
    def off(self):
        self.connection.execute_command(
            OutputOffCommandPacket(self.record_id)
        )

    def on(self, time: timedelta | None = None):
        if time is not None:
            time_seconds = time.total_seconds()
            if time_seconds > 0xFFFF:
                raise ValueError(f"Time cannot exceed {0xFFFF} total seconds")

            self.connection.execute_command(
                OutputOnTimedCommandPacket(self.record_id, time_seconds)
            )
        else:
            self.connection.execute_command(
                OutputOnCommandPacket(self.record_id)
            )
