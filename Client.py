import socket
import time
import sys
import threading
import cv2
import numpy as np
import pickle
from tkinter import*
from tkinter import messagebox as tkMessageBox
from tkinter import ttk
from RtpPacket import RtpPacket
import io
from PIL import Image, ImageTk

T_SEC = 1
BUFFER_SIZE = 1000
SERVER_HOST, SERVER_PORT = '127.0.0.1', 8888
CLIENT_HOST = '0.0.0.0'

class Client:
    def __init__(self, master, rtpPort, filename):
        # tkinter
        self.master = master
        self.master.title("video streaming")
        self.master.protocol("WM_DELETE_WINDOW", self.handler) # handle closing GUI window
        self.playMovieButton = False # toggle
        self.tkwindow()
        # videostreamer
        self.buffer = []
        self.playIndex = 0
        #RTP
        self.rtpPort = rtpPort
        self.frameNbr = 0
        #RTSP
        self.state = 'INIT' # 'INIT', 'READY', 'PLAYING'
        self.sessionID = 0
        self.rtspSeq = 0
        self.filename = filename
        self.requestSent = None
        self.SETUP_STR = 'SETUP {}\n1\n RTSP/1.0 RTP/UDP {}'.format(self.filename, self.rtpPort)
        self.PLAY_STR = 'PLAY \n2'
        self.PAUSE_STR = 'PAUSE \n3'
        self.TEARDOWN_STR = 'TEARDOWN \n4'
        self.connectToServer()
                    
    def connectToServer(self):
        # RTSP / TCP session
        self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtsp_socket.connect((SERVER_HOST, SERVER_PORT))
    
    def openRTPsocket(self):
        self.rtp_socket = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.rtp_socket.settimeout(0.5)
        self.rtp_socket.bind((CLIENT_HOST, self.rtpPort))

    def recvRtspReply(self):
        while True:
            try:
                data = self.rtsp_socket.recv(1024)
                if data:
                    print('### RTSP reply recieved: {}'.format(data))
                    self.parseRtspReply(data)
                #teardown
                if self.requestSent == 'TEARDOWN':
                    self.rtsp_socket.shutdown(socket.SHUT_RDWR)
                    self.rtsp_socket.close()        
                    break
            except: continue
    
    def parseRtspReply(self, data):
        lines = data.decode().split('\n')
        seqNum = int(lines[1].split(' ')[1])
        session = int(lines[2].split(' ')[1])
        if self.sessionID == 0: self.sessionID = session # new
        # Problem:
        # server seqNum in {1,2,3,4} while self.rtspSeq = self.rtspSeq +1 each request
        # print("seqNum= {}, self.rtspseq= {}".format(seqNum, self.rtspSeq))
        #if self.rtspSeq == seqNum:
        if self.sessionID == session and int(lines[0].split(' ')[1]) == 200:
            if self.requestSent == 'SETUP':
                self.state = 'READY'
                self.openRTPsocket()
            elif self.requestSent == 'PLAY':
                self.state = 'PLAYING'
            elif self.requestSent == 'PAUSE':
                self.state = 'READY'
                self.playRequestEvent.set()
            elif self.requestSent == 'TEARDOWN':
                self.state = 'INIT'
                self.rtp_socket.shutdown(socket.SHUT_RDWR)
                self.rtp_socket.close()
        #else: print("not in order")

    def listenRtp(self):    
        while True:
            try:
                data, addr = self.rtp_socket.recvfrom(80000)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    
                    currFrameNbr = int.from_bytes(rtpPacket.seqnum, "big")
                    '''
                    # problem (no need)
                    if currFrameNbr > self.frameNbr: # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.buffer.append(rtpPacket.getPayload())
                        print("self.buffer length = ",len(self.buffer))
                    '''
                    self.buffer.append(rtpPacket.getPayload())
                    if len(self.buffer) > BUFFER_SIZE:
                        self.buffer = []
                        self.playIndex = 0
                        self.bar.set(self.playIndex)
                    print('*** RTP reply received: ', currFrameNbr)
                if self.playRequestEvent.isSet():
                    break
            except: continue # handle out of time
            
    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = 'cache-' + str(self.sessionID) + '.jpg'
        file = open(cachename, "wb")
        file.write(data)
        file.close()
        return cachename

    def setupRequest(self):
        if self.state == 'INIT':
            threading.Thread(target=self.recvRtspReply).start()
            self.rtspSeq = self.rtspSeq + 1
            self.rtsp_socket.send(self.SETUP_STR.encode())
            self.requestSent = 'SETUP'

    def playRequest(self):
        if self.state == 'READY':
            threading.Thread(target=self.listenRtp).start()
            self.playRequestEvent = threading.Event()
            self.playRequestEvent.clear()
            self.rtspSeq = self.rtspSeq + 1
            self.rtsp_socket.send(self.PLAY_STR.encode())
            self.requestSent = 'PLAY'
            #self.playMovie()

    def pauseRequest(self):
        if self.state == 'PLAYING':
            self.rtspSeq = self.rtspSeq + 1
            self.rtsp_socket.send(self.PAUSE_STR.encode())
            self.requestSent = 'PAUSE'
            #self.stopMovie()
    
    def tearRequest(self):
        self.rtspSeq = self.rtspSeq + 1
        self.rtsp_socket.send(self.TEARDOWN_STR.encode())
        self.requestSent = 'TEARDOWN'   
        self.master.destroy() # Close the gui window
    
    def playMovie(self):
        self.runEvent = threading.Event()
        threading.Thread(target=self.run).start()

    def stopMovie(self):
        self.runEvent.set()

    def backwardMovie(self):
        self.playIndex = self.playIndex - 30*T_SEC
        if self.playIndex < 0 : self.playIndex = 0
        self.bar.set(self.playIndex)
        print("replay, frame # = ", self.playIndex)

    def forwardMovie(self):
        self.playIndex = self.playIndex + 30*T_SEC
        if self.playIndex > len(self.buffer) : self.playIndex = len(self.buffer)
        self.bar.set(self.playIndex)
        print("replay, frame # = ", self.playIndex)

    def play_pause_Movie(self):
        if self.playMovieButton == True:
            # pause
            self.playMovieButton = False
            self.stopMovie()
        else: # play
            self.playMovieButton = True
            self.playMovie()

    def run(self):
        while True:
            if self.runEvent.isSet():
                break
            if self.playIndex > len(self.buffer): self.playIndex = len(self.buffer)
            if self.playIndex < len(self.buffer):
                pilImage = Image.open(self.writeFrame(self.buffer[self.playIndex]))
                w = self.master.winfo_height() # current window height
                h = self.master.winfo_width() # current window width
                pilImage = pilImage.resize((h, w), Image.ANTIALIAS) # rescale
                imgtk = ImageTk.PhotoImage(pilImage)
                self.label.configure(image = imgtk, height=h, width=w) 
                self.label.image = imgtk
                self.playIndex += 1
                self.bar.set(self.playIndex) # update scrollbar
                #print(self.playIndex)
                time.sleep(1/30) # 30 frames per second
            self.playIndex = int(self.bar.get()) # update index by scrollbar
    
    def tkwindow(self):
        """Build GUI."""
        bottom_frame = Frame(self.master)
        bottom_frame.pack(side=BOTTOM)
        top_frame = Frame(self.master)
        top_frame.pack(side=TOP)
        # Create Setup button
        self.setup = Button(bottom_frame, width=3, height=1, bg='white')
        self.setup["text"] = "⚙"
        self.setup["command"] = self.setupRequest
        self.setup.pack(side=LEFT)
        # Create Play button        
        self.start = Button(bottom_frame, width=3, height=1, bg='white')
        self.start["text"] = "⬤"
        self.start["command"] = self.playRequest
        self.start.pack(side=LEFT)
        # Create backward button
        self.backward = Button(bottom_frame, width=3, height=1, bg='white')
        self.backward["text"] = "{}⏪".format(T_SEC)
        self.backward["command"] =  self.backwardMovie
        self.backward.pack(side=LEFT)
        # Create playMovie button
        self.play = Button(bottom_frame, width=3, height=1, bg='white')
        self.play["text"] = "⏯"
        self.play["command"] = self.play_pause_Movie
        self.play.pack(side=LEFT) 
        # Create forward button
        self.forward = Button(bottom_frame, width=3, height=1, bg='white')
        self.forward["text"] = "⏩{}".format(T_SEC)
        self.forward["command"] =  self.forwardMovie
        self.forward.pack(side=LEFT)
        # Create Pause button           
        self.pause = Button(bottom_frame, width=3, height=1, bg='white')
        self.pause["text"] = "■"
        self.pause["command"] = self.pauseRequest
        self.pause.pack(side=LEFT)
        # Create Teardown button
        self.teardown = Button(bottom_frame, width=3, height=1, bg='white')
        self.teardown["text"] = "🗑"
        self.teardown["command"] = self.tearRequest
        self.teardown.pack(side=LEFT)
        # Create a bar
        self.bar = ttk.Scale(bottom_frame, from_=0, to=BUFFER_SIZE, length=300)
        self.bar.pack(side=LEFT)
        # Create a label to display the movie
        self.label = Label(top_frame, bg='black')
        self.label.pack(side=TOP)

    def handler(self): # handle closing GUI window directly without teardown button
        """Handler on explicitly closing the GUI window."""
        self.pauseRequest()
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.tearRequest()
        else: # When the user presses cancel, resume playing.
            self.playRequest()
    

