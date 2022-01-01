import socket
import time
import sys

if __name__ == '__main__':
	
	SERVER_HOST, SERVER_PORT = '127.0.0.1', 8888
	CLIENT_HOST, CLIENT_PORT = '0.0.0.0', int(sys.argv[1])
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	client_socket.bind((CLIENT_HOST, CLIENT_PORT))
	client_socket.connect((SERVER_HOST, SERVER_PORT))
	RTSP_msgs = [
		'SETUP video.mjpeg\n1\n RTSP/1.0 RTP/UDP {}'.format(CLIENT_PORT),
		'PLAY \n2',
		'PAUSE \n3',
		'TEARDOWN \n4'
	]
	client_socket.send(RTSP_msgs[0].encode())
	# while True:
	# 	data = client_socket.recv(1024)
	# 	print('### RTSP reply received: {}'.format(data))
	for msg in RTSP_msgs:
		client_socket.send(msg.encode())
		data = client_socket.recv(1024)
		print('### RTSP reply received: {}'.format(data))
		time.sleep(0.5)
	client_socket.close()
	# while True:
	# 	data, addr = client_socket.recvfrom(1024)
	# 	print('### RTSP reply received: {}'.format(data))