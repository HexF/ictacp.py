from abc import ABC, abstractmethod


class Encryption(ABC):
    encryption_type=0
    def __init_subclass__(cls, encryption_type:int) -> None:
        cls.encryption_type = encryption_type

    @abstractmethod
    def encrypt(self, data: bytes) -> bytes:
        pass

    @abstractmethod
    def decrypt(self, data: bytes) -> bytes:
        pass

#TODO: Encrpytion (AES)
