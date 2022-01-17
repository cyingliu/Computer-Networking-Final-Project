import sys

HEADER_SIZE = 2 # only consider 2 bytes seq num

class RtpPacket:
	def __init__(self):
		self.seqnum = None
		self.payload = None

	def encode(self, seqnum, payload):
		self.seqnum = bytearray(seqnum.to_bytes(HEADER_SIZE, sys.byteorder))
		self.payload = payload

	def getPacket(self):
		return self.seqnum + self.payload

	def decode(self, bytestring):
		self.seqnum = bytestring[:HEADER_SIZE]
		self.payload = bytestring[HEADER_SIZE:]

	def getSeqNum(self):
		return int.from_bytes(self.seqnum, sys.byteorder)
		
	def getPayload(self):
		return self.payload