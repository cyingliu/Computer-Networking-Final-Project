import socket

if __name__ == '__main__':
	
	HOST, PORT = '127.0.0.1', 8888
	client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	client_socket.sendto('hello'.encode(), (HOST, PORT))
	while True:
		data, addr = client_socket.recvfrom(1024)
		print(data.decode(), addr)