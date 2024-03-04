import socket
from multiprocessing import Process

import cv2
import numpy as np

from base64 import b64encode, b64decode
from turbojpeg import TurboJPEG
from pickle import dumps, loads
from struct import pack, unpack, calcsize

from time import time, sleep
from loguru import logger as log

Mat = np.ndarray
jpeg = TurboJPEG()

class Frame:
    def cvt2bytesTurbo(frame: Mat) -> bytes:
        """
        Convert a cv2 frame to bytes with turbojpeg
        """
        return b64encode(jpeg.encode(frame))

    def cvt2bytes(frame: Mat) -> bytes:
        """
        Convert a cv2 frame to bytes
        """
        byteFrame = dumps(frame)
        return pack("Q", len(byteFrame))+byteFrame

    def cvt2frame(bytesFrame: bytes) -> Mat:
        """
        Convert bytes to cv2 frame
        """
        frameSize = unpack("Q", bytesFrame[:calcsize("Q")])[0]
        frame = bytesFrame[calcsize("Q"):calcsize("Q")+frameSize]
        return loads(frame)

class TCPSocketHandler:
    def __init__(self,
                 serverIP: str = '127.0.0.1',
                 serverPort: int = 8000
                 ) -> object:
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.serverAddr = (self.serverIP, self.serverPort)

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.isConnected = False
    
    def connect(self) -> bool:
        """
        Connect to the server
        """
        if self.isConnected:
            log.warning("Already connected to server")
            return True

        try:
            self.serverSocket.connect(self.serverAddr)
            self.isConnected = True
            log.success('Connected to server')
            return True
        except Exception as e:
            log.error(f"{e}")
            return False

    def disconnect(self) -> bool:
        """
        Disconnect from the server
        """
        if not self.isConnected:
            log.warning("Not connected to server")
            return True
        
        try:
            self.sendData('disconnect'.encode())
            self.serverSocket.close()
            self.isConnected = False
            log.success('Disconnected from server')
            return True
        
        except Exception as e:
            log.error(f"{e}")
            return False

    def sendData(self, data: bytes) -> bool:
        """
        Send data to the server
        """
        if not self.isConnected:
            log.error("Not connected to server")
            return False
        
        try:
            self.serverSocket.sendall(data)
            return True
        except Exception as e:
            log.error(f"{e}")
            return False
        
    def sendFrame(self, frame: Mat) -> bool:
        """
        Send a frame to the server
        """
        if not self.isConnected:
            log.error("Not connected to server")
            return False

        try:
            self.serverSocket.sendall(Frame.cvt2bytes(frame))
            return True
        except Exception as e:
            log.error(f"{e}")
            return False

class R2C:
    def __init__(self,
                 serverIP: str = '127.0.0.1',
                 serverPort: int = 8000
                 ) -> object:
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.serverAddr = (self.serverIP, self.serverPort)

        self.streams = {}
    
    def addStream(self, streamName: str = 'default') -> TCPSocketHandler:
        """
        Add a stream to the server
        """
        if streamName in self.streams:
            log.warning(f"Stream {streamName} already exists")
            return self.streams[streamName]
        
        try:
            self.streams[streamName] = TCPSocketHandler(self.serverIP, self.serverPort)
            self.streams[streamName].connect()
            log.success(f"Stream {streamName} added")
            return self.streams[streamName]
        except Exception as e:
            log.error(f"{e}")
            return False
    
    def setFrame(self, streamName: str, frame: Mat) -> bool:
        """
        Set a frame to the server
        """
        if streamName not in self.streams:
            log.warning(f"Stream {streamName} does not exist")
            return False

        try:
            self.streams[streamName].sendFrame(frame)
            return True
        except Exception as e:
            log.error(f"{e}")
            return False