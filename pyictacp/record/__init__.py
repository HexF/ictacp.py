from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from pyictacp.connection import Connection
from typing import Callable, List, Type
from pyictacp.packet.data import DataPacketData
from pyictacp.packet.command import RecordCommandPacket

class Record(ABC):
    data_class = DataPacketData
    data_request_command = RecordCommandPacket
    data_index_match = lambda rec, id: False

    def __init_subclass__(cls,
            data_class:Type[DataPacketData],
            data_request_command:Type[RecordCommandPacket],
            data_index_match: Callable[[DataPacketData, int], bool]
        ) -> None:

        cls.data_class = data_class
        cls.data_request_command = data_request_command
        cls.data_index_match = data_index_match
    
    def __init__(self, connection: Connection, record_id: int):
        self.record_id = record_id
        self.connection = connection
        self.last_updated: datetime = None
        

    def update(self):
        """Request the current state, and load onto the object
        """
        
        result = self.connection.execute_command(
            self.__class__.data_request_command(
                self.record_id
            )
        )
        if result is None:
            raise ValueError("Returned data was not data")

        data = None
        for component in result:
            if (isinstance(component, self.__class__.data_class)
                and self.__class__.data_index_match(component, self.record_id)):
                data = component

        if data is None:
            raise ValueError("No data was found")

        self._update(data)
        self.last_updated = datetime.utcnow()
        

    @abstractmethod
    def _update(self, data: DataPacketData):
        """Update the record with the given data
        """
        pass