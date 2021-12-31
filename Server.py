import socket
class Server:
	def __init__(self, clientAddr):
		self.clientAddr = clientAddr
	def processRTSPrequest(self, data):
		print(data.decode())

if __name__ == '__main__':

	HOST, PORT = '127.0.0.1', 8888
	server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # TCP: SOCK_STREAM, UDP: SOCK_DGRAM
	server_socket.bind((HOST, PORT))

	print('RTSP socket listening...')
	clients = {} # (addr: Server Object)
	while True:
		data, addr = server_socket.recvfrom(1024)
		if addr not in clients:
			clients[addr] = Server(addr)
		clients[addr].processRTSPrequest(data)


