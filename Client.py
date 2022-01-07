import socket
import time
import sys
import threading
import cv2
import numpy as np
import pickle

from RtpPacket import RtpPacket
from PIL import Image

def recvRtspReply(rtsp_socket):
	while True:
		data = rtsp_socket.recv(1024)
		if data:
			print('### RTSP reply recieved: {}'.format(data))

def listenRtp(rtp_socket, video_streamer):
	
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
			
			print('*** RTP reply received: {}'.format('data'))

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

if __name__ == '__main__':
	
	SERVER_HOST, SERVER_PORT = '127.0.0.1', 8888
	CLIENT_HOST, CLIENT_RTP_PORT = '0.0.0.0', int(sys.argv[1])
	# RTSP / TCP session
	rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	rtsp_socket.connect((SERVER_HOST, SERVER_PORT))
	# RTP / UDP session
	rtp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	rtp_socket.bind((CLIENT_HOST, CLIENT_RTP_PORT))

	video_streamer = VideoStreamer()
	video_streamer.run()

	RTSP_msgs = [
		'SETUP video.mjpeg\n1\n RTSP/1.0 RTP/UDP {}'.format(CLIENT_RTP_PORT),
		'PLAY \n2',
		'PAUSE \n3',
		'TEARDOWN \n4'
	]
	teardown_event = threading.Event()
	threading.Thread(target=recvRtspReply, args=(rtsp_socket,)).start()
	threading.Thread(target=listenRtp, args=(rtp_socket, video_streamer)).start()
	# SETUP
	rtsp_socket.send(RTSP_msgs[0].encode())
	time.sleep(0.5)
	# PLAY
	rtsp_socket.send(RTSP_msgs[1].encode())
	time.sleep(10)
	# PAUSE
	rtsp_socket.send(RTSP_msgs[2].encode())
	time.sleep(10)
	# TEARDOWN
	rtsp_socket.send(RTSP_msgs[3].encode())
	# close windows
	video_streamer.event.set()
	

