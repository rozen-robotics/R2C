from r2cAPI import TCPSocketHandler as tcp, R2C as rrc
import cv2 as cv
from time import time, sleep
from multiprocessing import Process


cap = cv.VideoCapture(0)


if __name__ == '__main__':
    host = rrc('192.168.0.101', 6969)

    host.addStream('raw')
    host.addStream('hsv')

    while True:
        raw = cap.read()[1]
        hsv = cv.cvtColor(raw, cv.COLOR_BGR2HSV)

        host.setFrame('raw', raw)
        host.setFrame('hsv', hsv)