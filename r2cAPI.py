import socket

import cv2
from base64 import b64encode, b64decode
from struct import pack
from pickle import dumps
import numpy as np

from time import time, sleep
from loguru import logger as log

Mat = np.ndarray


class Frame:
    def cvt2base64(frame: Mat) -> bytes:
        return b64encode(cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY,80]))
    
    def cvt2bytes(frame: Mat) -> bytes:
        byted_frame = dumps(frame)
        return pack("Q", len(byted_frame)) + byted_frame

class UDPSocketHandler:
    def __init__(self, 
                 port: int = 8000, 
                 buffer_size: int = 65536
                 ) -> object:
        self.port: int = port
        self.buffer_size: int = buffer_size

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.buffer_size)

        self.host_name: str = socket.gethostname()
        self.host_ip: str = socket.gethostbyname(self.host_name)
        self.socket_addr: tuple[str, int] = tuple(self.host, self.port)
        
        self.socket.bind(self.socket_addr)
        self.client_addr: str = self.socket.recvfrom(self.buffer_size)[1]
    
    def send_frame(self, frame: Mat) -> None:
        self.socket.sendto(self.cvtframe2base64(frame), self.socket_address)

class TCPSocketHandler:
    def __init__(self, 
                 hostIP: str = '127.0.0.1',
                 port: int = 8000
                 ) -> object:
        self.hostIP: str = hostIP
        self.port: int = port
        self.hostAddr: tuple[str, int] = (self.hostIP, self.port)

        self.hostSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.isConnected: bool = False

        self.connect()
        
    def connect(self) -> bool:
        self.hostSocket.connect(self.hostAddr)
        self.isConnected = self.hostSocket
        
        if not self.isConnected:
            log.warning("Can't connect to host")
            return False

        return True  
    
    def close(self) -> None:
        self.hostSocket.close()

    def sendFrame(self, frame: Mat) -> bool:
        if not self.isConnected:
            log.warning('Not connected to host')
            return False
        
        self.hostSocket.sendall(Frame.cvt2bytes(frame))
        return True


class R2C:
    def __init__(self, 
                 hostIP: str = '127.0.0.1',
                 logging: bool = True,
                 enableUDP: bool = True,
                 ) -> object:
        self.host_ip = hostIP
        self.logging = logging
        self.enableUDP = enableUDP

        self.connections = dict()
        self.usedPorts = list()

    def addStream(self, port: int = 8000) -> bool:
        # if port in self.usedPorts:
        #     if self.logging: 
        #         log.critical('Port already in use')
        #     return False

        self.connections[port] = TCPSocketHandler(self.host_ip, port) if self.enableUDP else UDPSocketHandler(port)
        self.usedPorts.append(port)

        if self.logging:
            if self.connections[port].isConnected: 
                log.success('Connected to host successfully')
            else:
                log.warning("Can't connect to host")

        return True
    
    def sendFrame(self, port: int, frame: Mat) -> bool:
        if port not in self.usedPorts:
            if self.logging:
                log.warning('Port connection not found. Connecting...')

            ret = self.addStream(port)
            if self.logging:
                if ret:
                    log.success('Connected to host successfully')
                else:
                    log.critical("Can't connect to host")
                    return False
                
        return self.connections[port].sendFrame(frame)
    
    def closeStream(self, port: int = 8000) -> bool:
        if port not in self.usedPorts:
            if self.logging:
                log.warning('Port connection not found.')
            return False

        self.connections[port].close()
        self.usedPorts.remove(port)
        
        if self.logging:
            log.success(f'Closed connection to port {port}')
        return True
    
    def closeAllStreams(self) -> bool:
        for port in self.usedPorts:
            self.closeStream(port)

        if self.logging:
            log.success('Closed all connections')
        
        self.connections = dict()
        self.usedPorts = list()
        
        return True