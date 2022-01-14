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

        # frame = frame.tobytes()
        self.framNum += 1

        print('----- Next Video Frame (# {}), length: {} -----'.format(self.framNum, len(frame)))
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 12]
        return cv2.imencode('.jpg', frame, encode_param)[1].tostring()

class LiveStreamAudio:
    def __init__(self):
        self.framNum = 0
        
        self.NUM_CHUNK_PER_FPS = 10
        self.RATE = 44100 # num frames per second
        self.CHUNK = int(44100 / 30 * self.NUM_CHUNK_PER_FPS) # num frame
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        
        p = pyaudio.PyAudio()
        self.stream = p.open(format=self.FORMAT,
                channels=self.CHANNELS,
                rate=self.RATE,
                input=True,
                frames_per_buffer=self.CHUNK)

    def getNextChunk(self):

        data = self.stream.read(self.CHUNK)
        self.framNum += 1
        print('----- Next Audio Chunk (# {}), length: {} -----'.format(self.framNum, len(data)))
        return data

