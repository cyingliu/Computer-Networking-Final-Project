import socket
import os
import threading
from random import randint
from VideoStream import VideoStream
class ServerWorker:
	def __init__(self, socket, clientAddr):
		self.rtsp_socket = socket
		self.clientAddr = clientAddr
		self.state = 'INIT' # 'INIT', 'READY', PLAYING'
		self.videoStream = None
		self.session = None
		self.event = None
		self.worker = None
		self.close = False
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
				filename = request[0].split(' ')[1]
				if os.path.isfile(filename):
					self.state = 'READY'
					self.session = randint(100000, 999999)
					self.videoStream = VideoStream(filename)
					self.replyRTSP('OK_200', seqNum)
				else:
					print('404 not found')
		elif requestType == 'PLAY':
			if self.state == 'READY':
				print('PLAY request received')
				self.state = 'PLAYING'
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
			# close RTP socket
		else:
			pass
	def sendRTP(self):
		pass
	def replyRTSP(self, code, seqNum):
		if code == 'OK_200':
			reply = 'RTSP/1.0 200 OK\nCSeq: {}\nSession: {}'.format(seqNum, self.session).encode()
			self.rtsp_socket.send(reply)

if __name__ == '__main__':

	HOST, PORT = '127.0.0.1', 8888
	rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # RTSP: TCP socket
	rtsp_socket.bind((HOST, PORT))


	print('RTSP socket listening...')
	rtsp_socket.listen(5)
	while True:
		rtsp_client, addr = rtsp_socket.accept()   # this accept {SockID,tuple object},tuple object = {clinet_addr,intNum}!!!
		ServerWorker(rtsp_client, addr).run()
	
	# clients = {} # (addr: Worker Object)
	# while True:
	# 	data, addr = server_socket.recvfrom(1024)
	# 	if addr not in clients:
	# 		clients[addr] = Worker(server_socket, addr)
	# 	clients[addr].processRTSPrequest(data)
	# 	if clients[addr].close == True:
	# 		del clients[addr]


