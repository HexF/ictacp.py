import logging
#logging.basicConfig(level=logging.DEBUG)

from pyictacp.checksum import ByteChecksum
from pyictacp.connection.tcp import TCPConnection
from pyictacp.client import ICTACPClient

connection = TCPConnection("192.168.1.5", 2345, checksum=ByteChecksum())
connection.connect()

client = ICTACPClient(connection=connection)

client.login("577231")
print("Logged in")

desc = client.panel_description()
print(desc)

inp = client.get_input(626)

while True:
    inp.update()
    print(inp.input_state)