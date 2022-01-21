import cv2
from PIL import Image
import numpy as np
class VideoStream:
    def __init__(self, filename):
        self.filename = filename
        #self.file = open(filename, 'rb')
        self.file = cv2.VideoCapture(filename)
        self.framNum = 0
    def getNextFrame(self):
        # get frame length
        (grabbed, frame) = self.file.read()
        if grabbed:
            #self.file.release()
            self.framNum += 1
        try:
            frame = Image.fromarray(frame)
            frame = frame.resize((160, 120))
            frame = np.array(frame)
            frame = frame.tobytes()
            print('----- Next Video Frame (# {}), length: {} -----'.format(self.framNum, len(frame)))
        except: pass
		
        return frame