import socket
import time
import sys

if __name__ == '__main__':
	
	SERVER_HOST, SERVER_PORT = '127.0.0.1', 8888
	CLIENT_HOST, CLIENT_PORT = '0.0.0.0', int(sys.argv[1])
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	client_socket.bind((CLIENT_HOST, CLIENT_PORT))
	RTSP_msgs = [
		'SETUP video.mjpeg\n1\n RTSP/1.0 RTP/UDP {}'.format(CLIENT_PORT),
		'PLAY \n2',
		'PAUSE \n3',
		'TEARDOWN \n4'
	]
	for msg in RTSP_msgs:
		client_socket.sendto(msg.encode(), (SERVER_HOST, SERVER_PORT))
		data, addr = client_socket.recvfrom(1024)
		print('### RTSP reply received: {}'.format(data))
		time.sleep(0.5)
	# while True:
	# 	data, addr = client_socket.recvfrom(1024)
	# 	print('### RTSP reply received: {}'.format(data))