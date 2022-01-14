import cv2
class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		#self.file = open(filename, 'rb')
		self.file = cv2.VideoCapture(filename)
		self.framNum = 0
	def getNextFrame(self):
		# get frame length
		'''
		framelength = int(bytearray(self.file.read(5)))
		if framelength:
			frame = self.file.read(framelength)
			if len(frame) != framelength:
				raise ValueError('Incomplete frame data')
			print('----- Next Frame (# {}), length: {} -----'.format(self.framNum, framelength))
		self.framNum += 1
		return frame
		'''
		(grabbed, frame) = self.file.read()
		if grabbed:
			#self.file.release()
			self.framNum += 1
		encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 12]
		return cv2.imencode('.jpg', frame, encode_param)[1].tostring()
		# return "Frame {}".format(self.framNum).encode()