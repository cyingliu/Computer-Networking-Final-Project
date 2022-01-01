import socket
import time
import sys
import threading

def recvRtspReply(rtsp_socket):
	while True:
		data = rtsp_socket.recv(1024)
		if data:
			print('### RTSP reply recieved: {}'.format(data))

def listenRtp(rtp_socket):
	while True:
		data, addr = rtp_socket.recvfrom(20480)
		if data:
			print('*** RTP reply received: {}'.format(data))

if __name__ == '__main__':
	
	SERVER_HOST, SERVER_PORT = '127.0.0.1', 8888
	CLIENT_HOST, CLIENT_RTP_PORT = '0.0.0.0', 7777
	# RTSP / TCP session
	rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	rtsp_socket.connect((SERVER_HOST, SERVER_PORT))
	# RTP / UDP session
	rtp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	rtp_socket.bind((CLIENT_HOST, CLIENT_RTP_PORT))
	RTSP_msgs = [
		'SETUP video.mjpeg\n1\n RTSP/1.0 RTP/UDP {}'.format(CLIENT_RTP_PORT),
		'PLAY \n2',
		'PAUSE \n3',
		'TEARDOWN \n4'
	]
	teardown_event = threading.Event()
	threading.Thread(target=recvRtspReply, args=(rtsp_socket,)).start()
	threading.Thread(target=listenRtp, args=(rtp_socket,)).start()
	# SETUP
	rtsp_socket.send(RTSP_msgs[0].encode())
	time.sleep(0.5)
	# PLAY
	rtsp_socket.send(RTSP_msgs[1].encode())
	time.sleep(1)
	# PAUSE
	rtsp_socket.send(RTSP_msgs[2].encode())
	time.sleep(0.5)
	# TEARDOWN
	rtsp_socket.send(RTSP_msgs[3].encode())

	# for msg in RTSP_msgs:
	# 	client_socket.send(msg.encode())
	# 	data = client_socket.recv(1024)
	# 	print('### RTSP reply received: {}'.format(data))
	# 	time.sleep(0.5)
