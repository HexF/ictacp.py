import sys,os
sys.path.append(os.path.dirname(os.path.dirname(sys.argv[0])))

from ictacp.command import RecordType
from ictacp.protocol import ACPProtocol
from ictacp.encryption import NoneEncryption
from ictacp.util import Checksum

import asyncio


import logging
logging.basicConfig(level=logging.DEBUG)


async def main():
    loop = asyncio.get_running_loop()

    on_conn_close = loop.create_future()

    def state_callback(type, id, new_state):
        print(type,id,new_state)

    transport, protocol = await loop.create_connection(
        lambda: ACPProtocol(NoneEncryption(), Checksum.CHECKSUM8, state_callback),
        '192.168.1.5', 2345
    )

    await protocol.login("577231")

    print("logged in")
    
    panel = await protocol.get_system_info()
    print(panel)

    for i in range(620, 630):
        await protocol.watch(RecordType.INPUT, i)

    try:
        await on_conn_close
    finally:
        transport.close()


asyncio.run(main())

    

