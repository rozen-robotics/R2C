from multiprocessing import Process
from loguru import logger as log 
from r2cAPI import *


if __name__ == '__main__':
    server = Server(serverPort=6969) # Bind your server port (must be >1023 and same to client)
    server.start()

    while True:
        client = server.getClient()

        log.info(f'\nClient time: {client.acceptTime}\nClient type: {client.clientType}')
        Process(target=client.handle).start()