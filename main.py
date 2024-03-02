from r2cAPI import R2C
import cv2 as cv


rrc = R2C(hostIP='192.168.0.101')
cap = cv.VideoCapture(0)


if __name__ == '__main__':
    rrc.addStream(port=8000)

    while cv.waitKey(1) != ord('q'):
        ret, frame = cap.read()

        hsvFrame = cv.cvtColor(frame, cv.COLOR_BGR2HSV)

        rrc.sendFrame(port=8000, frame=hsvFrame)
    rrc.closeAllStreams()