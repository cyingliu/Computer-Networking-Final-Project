import socket
import time
import sys
import threading
import cv2
import numpy as np
from PIL import Image
import pyaudio
import sounddevice as sd

from RtpPacket import RtpPacket

def recvRtspReply(rtsp_socket):
    while True:
        data = rtsp_socket.recv(1024)
        if data:
            print('### RTSP reply recieved: {}'.format(data))

def listenRtp_video(rtp_socket, video_streamer):
    
    while True:
        data, addr = rtp_socket.recvfrom(57800)
        if data:
            rtpPacket = RtpPacket()
            rtpPacket.decode(data)
            frame = rtpPacket.getPayload()  
            inp = np.asarray(bytearray(frame), dtype=np.uint8).reshape(120, 160, 3)
            im = Image.fromarray(inp)
            im = im.resize((640, 480))
            im = np.array(im)
            # original video stream (read mjpeg) need to decode, live steam (cv2 video capture) doesn't need to decode
            # i0 = cv2.imdecode(inp, cv2.IMREAD_COLOR) 
            video_streamer.addFrame(im)
            
            print('*** RTP reply received: {} video'.format(len(frame)))

def listenRtp_audio(rtp_socket, audio_streamer):
    
    while True:
        data, addr = rtp_socket.recvfrom(64100)
        if data:
            rtpPacket = RtpPacket()
            rtpPacket.decode(data)
            frame = rtpPacket.getPayload()
            audio_streamer.addFrame(frame)
                        
            print('*** RTP reply received: {} audio'.format(len(frame)))

class VideoStreamer:
    def __init__(self):
        self.buffer = []
        self.frameNum = 0
        self.event = threading.Event()
    def addFrame(self, frame):
        self.buffer.append(frame)
    def run(self):
        threading.Thread(target=self.playMovie).start()
    def playMovie(self):
        while True:
            if self.event.isSet():
                if len(self.buffer) > 0:
                    cv2.destroyAllWindows()
                    cv2.waitKey(1)
                    break
            if self.frameNum < len(self.buffer):
                cv2.imshow('frame', self.buffer[self.frameNum])
                cv2.waitKey(1)
                self.frameNum += 1

class AudioStreamer:
    def __init__(self):
        # sould be same as audio live streamer defined in server side
        self.RATE = 44100 # num frames per second
        
        self.buffer = []
        self.frameNum = 0
        self.event = threading.Event()

    def addFrame(self, frame):
        self.buffer.append(frame)
    def run(self):
        threading.Thread(target=self.playSound).start()
    def playSound(self):
        while True:
            if self.event.isSet():
                if len(self.buffer) > 0:
                    break
            if self.frameNum < len(self.buffer):
                frames = np.frombuffer(b''.join(self.buffer[self.frameNum: self.frameNum+2]), dtype=np.int16)
                print('Play audio length: {}'.format(len(frames)))
                sd.play(frames, samplerate=self.RATE * 2) # don't know why need to double
                sd.sleep(0.5)

                self.frameNum += 2 # two channels

if __name__ == '__main__':
    
    SERVER_HOST, SERVER_PORT = '127.0.0.1', 8888
    CLIENT_HOST, CLIENT_RTP_PORT_VIDEO, CLIENT_RTP_PORT_AUDIO = '0.0.0.0', 6666, 7777
    # RTSP / TCP session
    rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rtsp_socket.connect((SERVER_HOST, SERVER_PORT))
    # RTP / UDP session video
    rtp_socket_video = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    rtp_socket_video.bind((CLIENT_HOST, CLIENT_RTP_PORT_VIDEO))
    # RTP / UDP session audio
    rtp_socket_audio = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    rtp_socket_audio.bind((CLIENT_HOST, CLIENT_RTP_PORT_AUDIO))

    video_streamer = VideoStreamer()
    video_streamer.run()
    audio_streamer = AudioStreamer()
    audio_streamer.run()

    RTSP_msgs = [
        'SETUP video.mjpeg\n1\n RTSP/1.0 RTP/UDP {} {}'.format(CLIENT_RTP_PORT_VIDEO, CLIENT_RTP_PORT_AUDIO),
        'PLAY \n2',
        'PAUSE \n3',
        'TEARDOWN \n4'
    ]
    teardown_event = threading.Event()
    threading.Thread(target=recvRtspReply, args=(rtsp_socket,)).start()
    threading.Thread(target=listenRtp_video, args=(rtp_socket_video, video_streamer)).start()
    threading.Thread(target=listenRtp_audio, args=(rtp_socket_audio, audio_streamer)).start()
    # SETUP
    rtsp_socket.send(RTSP_msgs[0].encode())
    time.sleep(0.5)
    # PLAY
    rtsp_socket.send(RTSP_msgs[1].encode())
    time.sleep(20)
    # PAUSE
    rtsp_socket.send(RTSP_msgs[2].encode())
    time.sleep(10)
    # TEARDOWN
    rtsp_socket.send(RTSP_msgs[3].encode())
    # close windows
    video_streamer.event.set()
    

