class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		self.file = open(filename, 'rb')
		self.framNum = 0
	def getNextFrame(self):
		self.framNum += 1
		return "Frame {}".format(self.framNum).encode()