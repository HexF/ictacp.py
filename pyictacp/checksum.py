from abc import ABC, abstractmethod


class Checksum(ABC):
    length = 0
    def __init_subclass__(cls, length:int = 0) -> None:
        cls.length = length

    @abstractmethod
    def calculate(self, data: bytes) -> bytes:
        pass

class ByteChecksum(Checksum, length=1):    
    def calculate(self, data: bytes) -> bytes:
        return bytes([
            sum(data) % 256
        ])


#TODO: CRC16