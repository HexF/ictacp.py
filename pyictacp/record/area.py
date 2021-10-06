from __future__ import annotations
from pyictacp.connection import Connection
from pyictacp.record import Record
from pyictacp.packet.data import AreaStatusDataPacketData
from pyictacp.packet.command import ArmAreaCommandPacket, Disarm24AreaCommandPacket, DisarmAllAreaCommandPacket, DisarmAreaCommandPacket, ForceArmAreaCommandPacket, InstantArmAreaCommandPacket, RequestAreaStatusCommandPacket, StayArmAreaCommandPacket


class Area(Record,
        data_class=AreaStatusDataPacketData,
        data_request_command=RequestAreaStatusCommandPacket,
        data_index_match=lambda rec, id: rec.area_index == id):
    
    def __init__(self, connection: Connection, record_id: int):
        super().__init__(connection, record_id)
        self.area_state = None
        self.area_tamper_state = None
        self.alarm_active = None
        self.siren_active = None
        self.alarm_in_memory = None
        self.remote_armed = None
        self.instant_armed = None
        self.partial_armed = None

    def _update(self, data: AreaStatusDataPacketData):
        assert data.area_index == self.record_id
        self.area_state = data.area_state
        self.area_tamper_state = data.area_tamper_state
        self.alarm_active = data.alarm_active
        self.siren_active = data.siren_active
        self.alarm_in_memory = data.alarm_in_memory
        self.remote_armed = data.remote_armed
        self.instant_armed = data.instant_armed
        self.partial_armed = data.partial_armed

    def arm(self):
        self.connection.execute_command(
            ArmAreaCommandPacket(self.record_id)
        )

    def force_arm(self):
        self.connection.execute_command(
            ForceArmAreaCommandPacket(self.record_id)
        )
    
    def stay_arm(self):
        self.connection.execute_command(
            StayArmAreaCommandPacket(self.record_id)
        )

    def instant_arm(self):
        self.connection.execute_command(
            InstantArmAreaCommandPacket(self.record_id)
        )

    def disarm(self):
        self.connection.execute_command(
            DisarmAreaCommandPacket(self.record_id)
        )
    
    def disarm_all(self):
        self.connection.execute_command(
            DisarmAllAreaCommandPacket(self.record_id)
        )

    def disarm_24hr(self):
        self.connection.execute_command(
            Disarm24AreaCommandPacket(self.record_id)
        )