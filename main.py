from r2cAPI import R2C as rrc, Frame
import cv2 as cv
from time import time


if __name__ == '__main__':
    cap = cv.VideoCapture(0)

    host = rrc(serverIP='192.168.0.101', # Put your server IP
               serverPort=6969)          # Put your server Port (must be >1023)
    host.addStream('raw',  connectionType='Frame-Stream')
    host.addStream('data', connectionType='Data-Stream')
    host.addStream('hsv',  connectionType='HSV-Stream')


    fpsTmr = time()
    while cv.waitKey(1) != ord('q'):
        raw = cap.read()[1]
        hsv = cv.cvtColor(raw, cv.COLOR_BGR2HSV)

        fpsTmr = Frame.putFPS(raw, round(1 / (time() - fpsTmr)))

        cv.imshow('raw', raw)
        host.imshow('raw', raw)
        host.imshow('hsv', hsv)
        host.sendData('data', 'Hello, Host!')