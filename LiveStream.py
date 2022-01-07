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

        frame = frame.tobytes()
        self.framNum += 1

        # # get frame length
        # framelength = int(bytearray(self.file.read(5)))
        # if framelength:
        #   frame = self.file.read(framelength)
        #   if len(frame) != framelength:
        #       raise ValueError('Incomplete frame data')
        print('----- Next Frame (# {}), length: {} -----'.format(self.framNum, len(frame)))
        # self.framNum += 1
        return frame
        # return "Frame {}".format(self.framNum).encode()