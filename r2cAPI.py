import socket

import cv2
import numpy as np

from pickle import dumps, loads
from struct import pack, unpack, calcsize

from time import time
from loguru import logger as log


Mat = np.ndarray
Color = tuple[int, int, int]
ColorRange = tuple[Color, Color]


class HSV_Trackbars:
    def __init__(self) -> object:
        self.windowName = 'HSV Trackbars'
        self.colorRange: ColorRange = ((0, 0, 0), (180, 255, 255))
        
        cv2.namedWindow(self.windowName)
        cv2.createTrackbar('H[0]', self.windowName, 0, 180, lambda _: _) 
        cv2.createTrackbar('H[1]', self.windowName, 0, 180, lambda _: _) 
        cv2.createTrackbar('S[0]', self.windowName, 0, 255, lambda _: _) 
        cv2.createTrackbar('S[1]', self.windowName, 0, 255, lambda _: _) 
        cv2.createTrackbar('V[0]', self.windowName, 0, 255, lambda _: _)
        cv2.createTrackbar('V[1]', self.windowName, 0, 255, lambda _: _)
        
        cv2.setTrackbarPos('H[1]', self.windowName, 180)
        cv2.setTrackbarPos('S[1]', self.windowName, 255)
        cv2.setTrackbarPos('V[1]', self.windowName, 255)

    def getColor(self) -> ColorRange:
        self.colorRange = ((cv2.getTrackbarPos('H[0]', self.windowName),
                            cv2.getTrackbarPos('S[0]', self.windowName),
                            cv2.getTrackbarPos('V[0]', self.windowName)),
                           (cv2.getTrackbarPos('H[1]', self.windowName),
                            cv2.getTrackbarPos('S[1]', self.windowName),
                            cv2.getTrackbarPos('V[1]', self.windowName)))
        
        return self.colorRange

    def showMask(self, hsvFrame) -> None:
        self.getColor()
        self.mask = cv2.inRange(hsvFrame, self.colorRange[0], self.colorRange[1])

        cv2.imshow(self.windowName, self.mask)

class Frame:
    white: Color = 255, 255, 255

    def cvt2bytes(frame: Mat) -> bytes:
        """
        Convert a cv2 frame to bytes
        """
        byteFrame = dumps(frame)
        return pack("Q", len(byteFrame))+byteFrame

    def addDataPanel(frame: Mat, height: int = 40) -> Mat:
        return np.concatenate((frame, np.zeros((height, frame.shape[1], 3), dtype=np.uint8)), axis=0) 

    def putFPS(frame: Mat, FPS: int) -> float:
        cv2.putText(frame, 
                    'FPS: ' + str(FPS), 
                    (5, frame.shape[0]-5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.5, 
                    Frame.white, 
                    1)
        return time()

class TCPSocketHandler:
    def __init__(self,
                 serverIP: str = '127.0.0.1',
                 serverPort: int = 8000,
                 connectionType: str = 'None'
                 ) -> object:
        self.serverIP = serverIP
        self.serverPort = serverPort
        self.serverAddr = (self.serverIP, self.serverPort)
        self.connectionType = connectionType

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.isConnected = False
    
    def start(self) -> bool:
        self.connect()
        self.sendConnectionType()

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

    def sendConnectionType(self) -> bool:
        """
        Send the connection type to the server
        """
        if not self.isConnected:
            log.error("Not connected to server")
            return False
        
        try:
            self.serverSocket.sendall(self.connectionType.encode())
            log.success('Sent connection type')
            return True 
        except:
            log.error('Failed to send connection type')
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
    
    def addStream(self, 
                  streamName: str = 'default',
                  connectionType: str = 'None'
                  ) -> TCPSocketHandler:
        """
        Add a stream to the server
        """
        if streamName in self.streams:
            log.warning(f"Stream {streamName} already exists")
            return self.streams[streamName]
        
        try:
            self.streams[streamName] = TCPSocketHandler(self.serverIP, 
                                                        self.serverPort,
                                                        connectionType)
            self.streams[streamName].start()
            log.success(f"Stream {streamName} added")
            return self.streams[streamName]
        except Exception as e:
            log.error(f"{e}")
            return False
    
    def sendData(self, streamName: str, data: str) -> bool:
        """
        Set a frame to the server
        """
        if streamName not in self.streams:
            log.warning(f"Stream {streamName} does not exist")
            return False

        try:
            self.streams[streamName].sendData(data.encode())
            return True
        except Exception as e:
            log.error(f"{e}")
            return False
        
    def imshow(self, streamName: str, frame: Mat) -> bool:
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

class Client:
    def __init__(self, 
                 clientSocket: socket.socket,
                 clientAddress: tuple[str, int],
                 ) -> object:
        self.clientSocket = clientSocket
        self.clientAddress = clientAddress
        self.acceptTime: float = time()
        self.clientType: str = self.getClientType()

    def getClientType(self) -> str:
        """
        Get the client type
        """
        return self.clientSocket.recv(1024).decode()
    
    def handle(self) -> bool:
        log.info(f'\nHandle {self.clientType} from {self.clientAddress}')

        match self.clientType:
            case 'Frame-Stream':
                self.getStream()

            case 'Data-Stream':
                self.getData()

            case 'HSV-Stream':
                self.getStream(trackbars='HSV')

    def getData(self) -> None:
        while self.clientSocket:
            data = self.clientSocket.recv(1024).decode('utf-8')
            print(f'Received data from {self.clientAddress}: {data}') 

    def getStream(self, trackbars: str = 'Default') -> None:
        while self.clientSocket:
            data, payloadSize, fpsTmr = b'', calcsize("Q"), time()
            match trackbars:
                case 'Default':
                    cv2.namedWindow('Default window')

                case 'HSV':
                    hsvWindow = HSV_Trackbars()

            while cv2.waitKey(1) != ord('q'):
                while len(data) < payloadSize:
                    packet = self.clientSocket.recv(4*1024)
                    if not packet:
                        break
                    data += packet
                
                msgSize = unpack("Q", data[:payloadSize])[0]
                data = data[payloadSize:]

                while len(data) < msgSize:
                    data += self.clientSocket.recv(4*1024)

                frame = loads(data[:msgSize])
                data = data[msgSize:]

                match trackbars:
                    case 'Default':
                        # fpsTmr = Frame.putFPS(frame, round(1 / (time() - fpsTmr)))
                        cv2.imshow('Default window', frame)
                    
                    case 'HSV':
                        hsvWindow.showMask(frame)

            self.clientSocket.close()

class Server:
    def __init__(self,
                 serverPort: int = 8000
                 ) -> object:
        self.serverIP = socket.gethostbyname(socket.gethostname())
        self.serverPort = serverPort
        self.serverAddr = (self.serverIP, self.serverPort)

        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)    

    def start(self) -> bool:
        try:
            self.serverSocket.bind(self.serverAddr)
            log.success(f'Bind {self.serverAddr} succesfully. Listening...')
            self.serverSocket.listen()
            return True
        except:
            log.error(f'Bind {self.serverAddr} failed.')
            return False

    def getClient(self) -> Client | None:
        try:
            clientSocket, clientAddress = self.serverSocket.accept()
            log.success(f'Accept {clientAddress} succesfully.')
            return Client(clientSocket, clientAddress)
        except:
            log.error(f'Accept {clientAddress} failed.')
            return None
