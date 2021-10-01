class Encryption:
    def __init__(self, command_value):
        self.command_value = command_value
    
    def encrypt_packet(self, packet: bytes) -> bytes:
        return packet
    
    def decrypt_packet(self, packet: bytes) -> bytes:
        return packet


class NoneEncryption(Encryption):
    def __init__(self):
        super().__init__(0)

    