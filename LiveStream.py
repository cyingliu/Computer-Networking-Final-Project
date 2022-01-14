import cv2
class LiveStream:
    def __init__(self):
        self.framNum = 0
        self.cap = cv2.VideoCapture(0)
        # default: (640, 480), original payload length 921k bytes, exceed UDP limit 65k bytes
        # new payload length: 57600 bytes
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160) 
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 120)
    def getNextFrame(self):
        ret, frame = self.cap.read()

        # frame = frame.tobytes()
        self.framNum += 1

        print('----- Next Frame (# {}), length: {} -----'.format(self.framNum, len(frame)))
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 12]
        return cv2.imencode('.jpg', frame, encode_param)[1].tostring()
