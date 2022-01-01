class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		self.file = open(filename, 'rb')
		self.framNum = 0
	def getNextFrame(self):
		# get frame length
		framelength = int(bytearray(self.file.read(5)))
		if framelength:
			frame = self.file.read(framelength)
			if len(frame) != framelength:
				raise ValueError('Incomplete frame data')
			print('----- Next Frame (# {}), length: {} -----'.format(self.framNum, frame))
		self.framNum += 1
		return frame
		# return "Frame {}".format(self.framNum).encode()