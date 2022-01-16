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
import pyaudio

T_SEC = 1
BUFFER_SIZE = 1000
SERVER_HOST, SERVER_PORT = '127.0.0.1', 8888
CLIENT_HOST = '0.0.0.0'

class Client:
    def __init__(self, master, rtpPort_video, rtpPort_audio, filename):
        # tkinter
        self.master = master
        self.master.title("video streaming")
        self.master.protocol("WM_DELETE_WINDOW", self.handler) # handle closing GUI window
        self.playMovieButton = False # toggle
        self.tkwindow()
        self.audio()
        # videostreamer
        self.buffer_video = []
        self.buffer_audio = []
        self.playIndex_video = 0
        self.playIndex_audio = 0
        self.buffNum = 0
        self.RESET_STATE = False
        #RTP
        self.rtpPort_video = rtpPort_video
        self.rtpPort_audio = rtpPort_audio
        # self.frameNbr = 0
        #RTSP
        self.state = 'INIT' # 'INIT', 'READY', 'PLAYING'
        self.sessionID = 0
        self.rtspSeq = 0
        self.filename = filename
        self.requestSent = None
        self.SETUP_STR = 'SETUP {}\n1\n RTSP/1.0 RTP/UDP {} {}'.format(self.filename, self.rtpPort_video, self.rtpPort_audio)
        self.PLAY_STR = 'PLAY \n2'
        self.PAUSE_STR = 'PAUSE \n3'
        self.TEARDOWN_STR = 'TEARDOWN \n4'
        self.connectToServer()

        self.tearEvent = threading.Event()
                    
    def connectToServer(self):
        # RTSP / TCP session
        self.rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.rtsp_socket.connect((SERVER_HOST, SERVER_PORT))
    
    def openRTPsocket(self):
        self.rtp_socket_video = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.rtp_socket_video.settimeout(0.5)
        self.rtp_socket_video.bind((CLIENT_HOST, self.rtpPort_video))

        self.rtp_socket_audio = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.rtp_socket_audio.settimeout(0.5)
        self.rtp_socket_audio.bind((CLIENT_HOST, self.rtpPort_audio))

    def recvRtspReply(self):
        while True:
            if self.tearEvent.isSet():
                break
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
                self.rtp_socket_video.shutdown(socket.SHUT_RDWR)
                self.rtp_socket_video.close()
        #else: print("not in order")

    def listenRtp_audio(self):
        while True:
            if self.tearEvent.isSet():
                break
            try:
                data, addr = self.rtp_socket_audio.recvfrom(80000)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    currFrameNbr = rtpPacket.getSeqNum()
                    self.buffer_audio.append(rtpPacket.getPayload())
                    if currFrameNbr < self.buffNum * BUFFER_SIZE: # late packet
                        continue
                    # if self.RESET_STATE:
                        # self.playMovie()
                    if len(self.buffer_audio) > BUFFER_SIZE//10:
                        self.reset()

            except: continue
    def listenRtp_video(self):    
        while True:
            if self.tearEvent.isSet():
                break
            try:
                data, addr = self.rtp_socket_video.recvfrom(80000)
                if data:
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)
                    
                    currFrameNbr = rtpPacket.getSeqNum()
                    '''
                    # problem (no need)
                    if currFrameNbr > self.frameNbr: # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.buffer.append(rtpPacket.getPayload())
                        print("self.buffer length = ",len(self.buffer))
                    '''
                    if currFrameNbr < self.buffNum * BUFFER_SIZE: # late packet
                        continue
                    print("Current frame number: {}\t Frame number: {}".format(len(rtpPacket.getPayload()), currFrameNbr))
                    self.buffer_video.append(rtpPacket.getPayload())
                    # if self.RESET_STATE:
                        # self.playMovie()
                    if len(self.buffer_video) > BUFFER_SIZE:
                        self.reset() # clean both buffer and update total frame number
                    # print('*** RTP reply received: ', currFrameNbr)
                if self.playRequestEvent.isSet():
                    break
            except: continue # handle out of time
    def reset(self):
        print('RESETTING BUFFER')
        self.buffer_video = []
        self.buffer_audio = []
        self.playIndex_video = 0
        self.playIndex_audio = 0
        self.bar.set(self.playIndex_video)
        self.buffNum += 1
        # self.runEvent.set()
        # self.RESET_STATE = True

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = 'cache-' + str(self.sessionID) + '.jpg'
        file = open(cachename, "wb")
        file.write(data)
        file.close()
        return cachename

    def setupRequest(self):
        if self.state == 'INIT':
            t = threading.Thread(target=self.recvRtspReply)
            t.setDaemon(True)
            t.start()
            self.rtspSeq = self.rtspSeq + 1
            self.rtsp_socket.send(self.SETUP_STR.encode())
            self.requestSent = 'SETUP'

    def playRequest(self):
        if self.state == 'READY':
            t = threading.Thread(target=self.listenRtp_video)
            t.setDaemon(True)
            t.start()
            t = threading.Thread(target=self.listenRtp_audio)
            t.setDaemon(True)
            t.start()
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
        self.tearEvent.set()   
        self.master.destroy() # Close the gui window
        self.master.quit()
    
    def playMovie(self):
        self.runEvent = threading.Event()
        self.playIndex_video = ((len(self.buffer_video) - 1) // 10) * 10
        self.playIndex_audio = ((len(self.buffer_video) - 1) // 10) * 10 + 10

        # threading.Thread(target=self.run_audio_video).start() # not working
        t = threading.Thread(target=self.run_video)
        t.setDaemon(True)
        t.start()
        t = threading.Thread(target=self.run_audio)
        t.setDaemon(True)
        t.start()
    def stopMovie(self):
        self.runEvent.set()

    def backwardMovie(self):
        self.playIndex_video = ((self.playIndex_video - 30*T_SEC)//10) * 10
        self.playIndex_audio = ((self.playIndex_video - 30*T_SEC)//10) * 10 + 10
        if self.playIndex_video < 0 : self.playIndex_video = 0
        if self.playIndex_audio < 0 : self.playIndex_audio = 0
        self.bar.set(self.playIndex_video)
        self.runEvent.Set()
        print("replay, frame # = ", self.playIndex_video)

    def forwardMovie(self):
        self.playIndex_video = ((self.playIndex_video + 30*T_SEC)//10) * 10
        self.playIndex_audio = ((self.playIndex_video + 30*T_SEC)//10) * 10 + 10
        if self.playIndex_video > len(self.buffer_video) : self.playIndex_video = len(self.buffer_video)
        if self.playIndex_audio > len(self.buffer_audio) * 10 : self.playIndex_audio = len(self.buffer_audio) * 10
        self.bar.set(self.playIndex_video)
        self.runEvent.Set()
        print("replay, frame # = ", self.playIndex_video)

    def play_pause_Movie(self):
        if self.playMovieButton == True:
            # pause
            self.playMovieButton = False
            self.stopMovie()
        else: # play
            self.playMovieButton = True
            self.playMovie()
    def play_audio_chunk(self):
        self.stream.write(self.buffer_audio[self.playIndex_audio//10])
        self.playIndex_audio += 10 # NUM_FRAME_PER_CHUNK
    def run_audio_video(self): # not working
        while  True:
            if self.tearEvent.isSet():
                break
            if self.runEvent.isSet():
                break
            if self.playIndex_audio > len(self.buffer_audio) * 10: self.playIndex_audio = len(self.buffer_audio) * 10
            if self.playIndex_video > len(self.buffer_video): self.playIndex_video = len(self.buffer_video)
            if self.playIndex_audio < len(self.buffer_audio) * 10:
                threading.Thread(target=self.play_audio_chunk()).start()
            self.playIndex_audio = (int(self.bar.get())//10)*10 + 10
            for i in range(5):
                if self.playIndex_video < len(self.buffer_video):
                    if self.runEvent.isSet():
                        break
                    inp = np.asarray(bytearray(self.buffer_video[self.playIndex_video]), dtype=np.uint8).reshape(90, 160, 3)
                    inp = inp[:, :, [2, 1, 0]]
                    pilImage = Image.fromarray(inp)

                    w = self.master.winfo_height() # current window height
                    h = self.master.winfo_width() # current window width
                    pilImage = pilImage.resize((h, w)) # rescale # , Image.ANTIALIAS
                    imgtk = ImageTk.PhotoImage(pilImage)
                    self.label.configure(image = imgtk, height=h, width=w) 
                    self.label.image = imgtk
                    self.playIndex_video += 2
                    self.bar.set(self.playIndex_video) # update scrollbar
                    time.sleep(1/30)
                self.playIndex_video = int(self.bar.get())

    def run_audio(self):
        
        while True:
            if self.tearEvent.isSet():
                break
            if self.runEvent.isSet():
                break
            if self.playIndex_audio > len(self.buffer_audio) * 10: 
                self.playIndex_audio = len(self.buffer_audio) * 10
                print('audio full, {}/{}'.format(self.playIndex_audio, len(self.buffer_audio)*10))
            if self.playIndex_audio < len(self.buffer_audio) * 10 and len(self.buffer_audio) != 0:
                time_start = time.time()
                print('Audio Index: {}/{}'.format(self.playIndex_audio, len(self.buffer_audio)*10))
                time.sleep(1/30) # wait for listenRTP_audio thread to finish pushing
                try:
                    self.stream.write(self.buffer_audio[self.playIndex_audio//10])
                except:
                    print('*** {}/{}'.format(self.playIndex_video, len(self.buffer_audio)*10))
                self.playIndex_audio += 10 # NUM_FRAME_PER_CHUNK
                time_end = time.time()
                print('\t\tPlay audio delay: {}'.format(time_end-time_start))
                self.playIndex_audio = (int(self.bar.get())//10)*10 + 10 # update index by scrollbar
    def run_video(self):
        # self.playIndex_video = (len(self.buffer_video) - 1) // 10 * 10
        while True:
            if self.runEvent.isSet():
                break
            if self.playIndex_video > len(self.buffer_video): self.playIndex_video = len(self.buffer_video)
            if self.playIndex_video < len(self.buffer_video) and len(self.buffer_video) != 0:
                time_start = time.time()
                print('\t\t\t\tImage Index: {}/{}'.format(self.playIndex_video, len(self.buffer_video)))
                # pilImage = Image.open(self.writeFrame(self.buffer_video[self.playIndex_video]))
                inp = np.asarray(bytearray(self.buffer_video[self.playIndex_video]), dtype=np.uint8).reshape(160, 90, 3) # (height, width, 3)
                inp = inp[:, :, [2, 1, 0]]
                pilImage = Image.fromarray(inp)

                # inp = np.array(pilImage)
                # pilImage = Image.fromarray(inp)
                w = self.master.winfo_height() # current window height
                h = self.master.winfo_width() # current window width
                pilImage = pilImage.resize((h, w)) # rescale # , Image.ANTIALIAS
                imgtk = ImageTk.PhotoImage(pilImage)
                self.label.configure(image = imgtk, height=h, width=w) 
                self.label.image = imgtk
                self.playIndex_video += 2
                self.bar.set(self.playIndex_video) # update scrollbar
                #print(self.playIndex)
                time.sleep(1/30) # 30 frames per second
                time_end = time.time()
                print('\t\t\t\t\tShow image delay: {}'.format(time_end-time_start))
            self.playIndex_video = int(self.bar.get()) # update index by scrollbar
    
    def audio(self):
        p = pyaudio.PyAudio()
        self.framNum = 0
        
        self.NUM_CHUNK_PER_FPS = 10
        self.RATE = 44100 # num frames per second
        self.CHUNK = int(44100 / 30 * self.NUM_CHUNK_PER_FPS) # num frame
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        # define callback
        
        self.stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        output=True,
                        ) # stream_callback=self.callback
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
    

