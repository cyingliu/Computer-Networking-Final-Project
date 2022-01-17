import cv2
import pyaudio
import time
from PIL import Image
import numpy as np


class LiveStreamVideo:
    def __init__(self):
        self.framNum = 0
        self.cap = cv2.VideoCapture(0)

    def getNextFrame(self):
        self.framNum += 1
        ret, frame = self.cap.read()
        try:
            frame = Image.fromarray(frame)
            frame = frame.resize((160, 120))
            frame = np.array(frame)
            frame = frame.tobytes()
            print('----- Next Video Frame (# {}), length: {} -----'.format(self.framNum, len(frame)))
        except: pass
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
        data = self.stream.read(self.CHUNK)
        self.buffer.append(data)
        # self.stream.stop_stream()
        self.framNum += self.NUM_FRAME_PER_CHUNK
        print('\t\t----- Next Audio Chunk (# {}), length: {} -----'.format(self.framNum, len(data)))
        return data

