import cv2
import pyaudio
import time
import numpy as np
from PIL import Image
class LiveStreamVideo:
    def __init__(self):
        self.framNum = 0
        self.cap = cv2.VideoCapture(0)
        # default: (640, 480), original payload length 921k bytes, exceed UDP limit 65k bytes
        # new payload length: 57600 bytes
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 160) # 160
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 90) # 120 # match the width/height ratio of your camera
    def getNextFrame(self):
        ret, frame = self.cap.read()
        # edited part: trans to PIL
        # warning: the shape would be reversed
        pilImage = Image.fromarray(frame)
        pilImage = pilImage.resize((90,160))
        frame = np.array(pilImage)
        cv2.imshow('frame', frame)
        cv2.waitKey(1)

        frame = frame.tobytes()
        self.framNum += 1
        
        print('----- Next Video Frame (# {}), length: {} -----'.format(self.framNum, len(frame)))
        # encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 12]
        # return cv2.imencode('.jpg', frame)[1].tostring()
        return frame

class LiveStreamAudio:
    def __init__(self):
        self.framNum = 0
        
        self.NUM_FRAME_PER_CHUNK = 10
        self.RATE = 44100 # num frames per second
        self.CHUNK = int(44100 / 30 * self.NUM_FRAME_PER_CHUNK) # num frame
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2

        self.buffer = []
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK)
        # self.stream.stop_stream() # for the first chunk delay

    def getNextChunk(self):
        # self.stream.start_stream()
        data = self.stream.read(self.CHUNK,exception_on_overflow = False)
        self.buffer.append(data)
        # self.stream.stop_stream()
        self.framNum += self.NUM_FRAME_PER_CHUNK
        print('----- Next Audio Chunk (# {}), length: {} -----'.format(self.framNum, len(data)))
        return data
