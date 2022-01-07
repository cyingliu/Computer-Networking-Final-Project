import cv2
import pyaudio

class LiveStreamVideo:
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

        # print('----- Video Next Frame (# {}), length: {} -----'.format(self.framNum, len(frame)))
        
        return frame

class LiveStreamAudio:
    def __init__(self):
        self.CHUNK = 16000 # num frame
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100 # num frames per second
        
        self.p = pyaudio.PyAudio()

        self.stream = self.p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)
        self.framNum = 0

    def getNextFrame(self):

        frame = self.stream.read(self.CHUNK, exception_on_overflow = False)
        self.framNum += 1
        print('----- Audio Next Frame (# {}), length: {} -----'.format(self.framNum, len(frame)))
        return frame