from enum import Enum


class Checksum(Enum):
    NONE = 0
    CHECKSUM8 = 1
    CRC16 = 2

def calculate_checksum(packet: bytes, checksum: Checksum) -> bytes:
    if checksum == Checksum.NONE:
        return bytes([])
    
    elif checksum == Checksum.CHECKSUM8:
        return bytes([
            sum([int(i) for i in packet]) % 256
            ])
    else:
        raise NotImplementedError("%s is not a supported checksum" % checksum)
