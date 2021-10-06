from __future__ import annotations
from abc import ABC, abstractmethod

from datetime import timedelta
from pyictacp.connection import Connection
from pyictacp.checksum import Checksum
from pyictacp.encryption import Encryption
from typing import List
from pyictacp.typez import ByteOrder, PanelInformation
from pyictacp.packet.data import DataPacketData, FirmwareBuildDataPacketData, FirmwareTypeDataPacketData, FirmwareVersionDataPacketData, PanelHardwareVersionDataPacketData, PanelSerialNumberDataPacketData
from pyictacp.packet.command import CommandPacket, InactivityTimeCommandPacket, LoginCommandPacket, LogoutCommandPacket, PanelDescriptionCommandPacket, PollCommandPacket
from pyictacp.record.area import Area
from pyictacp.record.door import Door
from pyictacp.record.input import Input
from pyictacp.record.output import Output
from pyictacp.record.troubleinput import TroubleInput
from pyictacp.record.variable import Variable


class ICTACPClient(ABC):
    def __init__(self, connection: Connection):
        self.connection = connection
        self.logged_in = False
        self.pin = ""

    

    def poll(self) -> bool:
        """Polls the controller
        """
        self.connection.execute_command(
            PollCommandPacket(),
            requires_login=False
        )
        
    def panel_description(self) -> PanelInformation:
        """Returns serial number, hardware version, firmware type, version and build
        """
        res = self.connection.execute_command(
            PanelDescriptionCommandPacket()
        )

        info: PanelInformation = {}

        if res is not None:
            for component in res:
                if isinstance(component, PanelSerialNumberDataPacketData):
                    info['serial_number'] = component.serial_number
                elif isinstance(component, PanelHardwareVersionDataPacketData):
                    info['hardware_version'] = component.hardware_version
                elif isinstance(component, FirmwareTypeDataPacketData):
                    info['firmware_type'] = component.firmware_type
                elif isinstance(component, FirmwareVersionDataPacketData):
                    info['firmware_version'] = component.firmware_version
                elif isinstance(component, FirmwareBuildDataPacketData):
                    info['firmware_build'] = component.firmware_build

            return info
            
        
        raise ValueError("ACK Packet was returned whilst expecting data")


    def login(self, pin_number: str):
        """Attempts a login to the controller
        """
        
        # Will raise exception if invalid login
        self.connection.execute_command(
            LoginCommandPacket(pin_number)
        )

        self.pin = pin_number
        self.logged_in = True

    def logout(self):
        """Logs out from the controller
        """

        if self.logged_in:
            # No use logging out if we aren't logged in
            self.connection.execute_command(
                LogoutCommandPacket()
            )
            self.logged_in = False
            self.pin = ""

    def inactivity_timeout(self, timespan: timedelta):
        """Set the inactivity timeout
        """
        total_seconds = int(timespan.total_seconds())

        if timespan > timedelta(minutes=100):
            raise ValueError("Timespan cannot be larger than 100 minutes")

        self.connection.execute_command(
            InactivityTimeCommandPacket(
                total_seconds
            )
        )

    #TODO: Monitor
    #TODO: Events

    def get_area(self, area_id: int) -> Area:
        area = Area(connection=self.connection, record_id=area_id)
        area.update()
        return area
    
    def get_door(self, door_id: int) -> Door:
        door = Door(connection=self.connection, record_id=door_id)
        door.update()
        return door

    def get_input(self, input_id: int) -> Input:
        inp = Input(connection=self.connection, record_id=input_id)
        inp.update()
        return inp

    def get_output(self, output_id: int) -> Output:
        out = Output(connection=self.connection, record_id=output_id)
        out.update()
        return out

    def get_trouble_input(self, trouble_input_id: int) -> TroubleInput:
        trouble_inp = TroubleInput(connection=self.connection, record_id=trouble_input_id)
        trouble_inp.update()
        return trouble_inp

    def get_variable(self, variable_id: int) -> Variable:
        var = Variable(connection=self.connection, record_id=variable_id)
        var.update()
        return var




    
