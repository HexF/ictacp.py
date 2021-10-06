from pyictacp.connection import Connection
from . import Record
from ..packet.data import VariableStatusDataPacketData
from ..packet.command import GetVariableCommandPacket, SetVariableCommandPacket

class Variable(Record,
        data_class = VariableStatusDataPacketData,
        data_request_command = GetVariableCommandPacket,
        data_index_match = lambda rec, id: rec.variable_index == id):

    def __init__(self, connection: Connection, record_id: int):
        super().__init__(connection, record_id)
        self.variable_value = None

    def set_value(self, new_value: int):
        if new_value > 0xFFFF:
            raise ValueError(f"new value is larger than {0xFFFF}")

        self.connection.execute_command(
            SetVariableCommandPacket(
                self.record_id,
                new_value
            )
        )

    def __get__(self, instance, owner) -> int:
        self.update()
        return self.variable_value
    
    def __set__(self, instance, new_value:int):
        self.set_value(
            new_value
        )



