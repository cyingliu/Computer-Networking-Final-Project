import socket
import os
import threading
from random import randint
from LiveStream import LiveStream
from RtpPacket import RtpPacket

class ServerWorker:
	def __init__(self, socket, clientAddr, live_stream):
		self.rtsp_socket = socket
		self.rtp_socket = None
		self.rtp_addr = clientAddr[0]
		self.rtp_port = None
		self.state = 'INIT' # 'INIT', 'READY', PLAYING'
		self.live_stream = live_stream
		self.session = None
		self.event = None
		self.worker = None

	def run(self):
		threading.Thread(target=self.receiveRTSPrequest).start()
	def receiveRTSPrequest(self):
		while True:
			data = self.rtsp_socket.recv(1024)
			if data:
				self.processRTSPrequest(data)
	def processRTSPrequest(self, data):
		print('### RTSP request received: {}'.format(data))
		request = data.decode().split('\n')
		requestType = request[0].split(' ')[0]
		seqNum = int(request[1])
		if requestType == 'SETUP':
			if self.state == 'INIT':
				print('SETUP request received')
				self.state = 'READY'
				self.session = randint(100000, 999999)
				self.rtp_port = int(request[2].split(' ')[-1])
				self.replyRTSP('OK_200', seqNum)
				
		elif requestType == 'PLAY':
			if self.state == 'READY':
				print('PLAY request received')
				self.state = 'PLAYING'
				self.rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				self.event = threading.Event()
				self.worker = threading.Thread(target=self.sendRTP)
				self.worker.start()
				self.replyRTSP('OK_200', seqNum)
		elif requestType == 'PAUSE':
			if self.state == 'PLAYING':
				print('PAUSE request received')
				self.state = 'READY'
				self.event.set()
				self.replyRTSP('OK_200', seqNum)
		elif requestType == 'TEARDOWN':
			print('TEARDOWN request received')
			self.event.set()
			self.replyRTSP('OK_200', seqNum)
			self.rtp_socket.close()
		else:
			pass
	def sendRTP(self):
		
		while True:
			if self.event.isSet(): # PAUSE, TEARDOWN
				break
			self.event.wait(0.05)
			data = self.live_stream.getNextFrame()
			framNum = self.live_stream.framNum

			self.rtp_socket.sendto(self.makeRtpPacket(data, framNum), (self.rtp_addr, self.rtp_port))

	def makeRtpPacket(self, payload, framNum):
		rtpPacket = RtpPacket()
		rtpPacket.encode(framNum, payload)
		return rtpPacket.getPacket()
	
	def replyRTSP(self, code, seqNum):
		if code == 'OK_200':
			reply = 'RTSP/1.0 200 OK\nCSeq: {}\nSession: {}'.format(seqNum, self.session).encode()
			self.rtsp_socket.send(reply)

if __name__ == '__main__':

	HOST, PORT = '127.0.0.1', 8888
	rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # RTSP: TCP socket
	rtsp_socket.bind((HOST, PORT))

	# to avoid delay, open live stream before listening
	live_stream = LiveStream()
	print('RTSP socket listening...')
	rtsp_socket.listen(5)
	while True:
		rtsp_client, addr = rtsp_socket.accept()   # this accept {SockID,tuple object},tuple object = {clinet_addr,intNum}!!!
		ServerWorker(rtsp_client, addr, live_stream).run()
