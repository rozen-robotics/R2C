import cv2 as cv
from time import time, sleep
from r2cAPI import *
from threading import Thread

if __name__ == '__main__':
    cap = cv.VideoCapture(0)

    host = R2C(serverIP='192.168.201.42', # Put your server IP
               serverPort=6969)          # Put your server Port (must be >1023)
    host.addStream('hsv',  connectionType='HSV-Stream')
    host.addStream('raw',  connectionType='Frame-Stream')
    # host.addStream('data', connectionType='Data-Stream')

    
    fpsTmr = time()
    while True:
        raw = cap.read()[1]
        hsv = cv.cvtColor(raw, cv.COLOR_BGR2HSV)

        fpsTmr = Frame.putFPS(raw, round(1 / (time() - fpsTmr)))

        host.imshow('hsv', hsv)
        host.imshow('raw', raw)
        # Thread(tqarget=host.imshow, args=('raw', raw)).start()
        # host.print('data', 'Hello, Host!')
