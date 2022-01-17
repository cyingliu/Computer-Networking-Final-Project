import os
import sys
import socket
import threading
from random import randint
from LiveStream import LiveStreamVideo, LiveStreamAudio
from RtpPacket import RtpPacket
import speech_recognition as sr
import wave
import time


class ServerWorker:
    def __init__(self, socket, clientAddr, live_stream_video, live_stream_audio):
        self.rtsp_socket = socket
        self.rtp_socket_video = None
        self.rtp_socket_audio = None
        self.rtp_socket_word = None
        self.rtp_addr = clientAddr[0]
        self.rtp_port_video = None
        self.rtp_port_audio = None
        self.rtp_port_word = None
        self.state = 'INIT' # 'INIT', 'READY', PLAYING'
        self.live_stream_video = live_stream_video
        self.live_stream_audio = live_stream_audio
        self.session = None
        self.event = None
        self.worker_video = None
        self.worker_audio = None
        self.framNum_video = 0 # for aligning video and audio
        self.framNum_audio = 0

    def run(self):
        threading.Thread(target=self.receiveRTSPrequest).start()

    def receiveRTSPrequest(self):
        while True:
            data = self.rtsp_socket.recv(1024)
            if data:
                self.processRTSPrequest(data)

    def processRTSPrequest(self, data):
        print('### RTSP request received: {}'.format(data))
        request = data.decode().split('\n')
        requestType = request[0].split(' ')[0]
        seqNum = int(request[1])
        if requestType == 'SETUP':
            if self.state == 'INIT':
                print('SETUP request received')
                self.state = 'READY'
                self.session = randint(100000, 999999)
                self.rtp_port_video = int(request[2].split(' ')[-3])
                self.rtp_port_audio = int(request[2].split(' ')[-2])
                self.rtp_port_word = int(request[2].split(' ')[-1])
                self.replyRTSP('OK_200', seqNum)               
        elif requestType == 'PLAY':
            if self.state == 'READY':
                print('PLAY request received')
                self.state = 'PLAYING'
                self.rtp_socket_video = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.rtp_socket_audio = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.rtp_socket_word = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.event = threading.Event()
                self.worker = threading.Thread(target=self.sendRTP_video_and_audio)
                self.worker.start()
                self.replyRTSP('OK_200', seqNum)
        elif requestType == 'PAUSE':
            if self.state == 'PLAYING':
                print('PAUSE request received')
                self.state = 'READY'
                self.event.set()
                self.replyRTSP('OK_200', seqNum)
        elif requestType == 'TEARDOWN':
            print('TEARDOWN request received')
            self.event.set()
            self.replyRTSP('OK_200', seqNum)
            self.worker.join()
            self.rtp_socket_video.close()
            self.rtp_socket_audio.close()
            self.rtp_socket_word.close()
        else: pass

    def asr(self, framNum):
        WAV_OUTPUT_FILE = os.path.join('cache', '{}.wav'.format(self.session))
        wf = wave.open(WAV_OUTPUT_FILE, 'wb')
        wf.setnchannels(self.live_stream_audio.CHANNELS)
        wf.setsampwidth(self.live_stream_audio.p.get_sample_size(self.live_stream_audio.FORMAT))
        wf.setframerate(self.live_stream_audio.RATE)
        wf.writeframes(b''.join(self.live_stream_audio.buffer[framNum//10-10:framNum//10]))
        wf.close()
        r = sr.Recognizer()
        WAV = sr.AudioFile(WAV_OUTPUT_FILE)
        with WAV as source:
            audio = r.record(source)
        output = r.recognize_google(audio,  language="zh-TW", show_all=True)
        if len(output) > 0:
            sent = output['alternative'][0]['transcript']
        else:
            sent = ""
        self.rtp_socket_word.sendto(self.makeRtpPacket(sent.encode(), framNum), (self.rtp_addr, self.rtp_port_word))
        # print(framNum, sent)

    def sendRTP_video_and_audio(self):
        while  True:
            tot_start_time = time.time()
            if self.event.isSet():
                asr_thread.join()
                break
            # audio, delay 0.3 sec
            start_time=time.time()
            data = self.live_stream_audio.getNextChunk() # delay 0-0.008 sec
            framNum = self.live_stream_video.framNum
            if framNum > 9:
                asr_thread = threading.Thread(target=self.asr, args=(framNum,))
                asr_thread.start()
            self.rtp_socket_audio.sendto(self.makeRtpPacket(data, framNum), (self.rtp_addr, self.rtp_port_audio))
            end_time = time.time()
            print('Total Audio Delay: {}'.format(end_time-start_time))
            # video, delay 0.002
            for i in range(10):
                if self.event.isSet():
                    break
                start_time=time.time()
                data = self.live_stream_video.getNextFrame() # delay 0.002 sec
                framNum = self.live_stream_video.framNum
                self.framNum_video = framNum
                self.rtp_socket_video.sendto(self.makeRtpPacket(data, framNum), (self.rtp_addr, self.rtp_port_video))
                end_time = time.time()
                print('Total Video Delay: {}'.format(end_time-start_time))
            tot_end_time = time.time()
            # print('Total 10 frame delay: {} ({})'.format(tot_end_time-tot_start_time, tot_end_time-tot_start_time-1/3))

    def makeRtpPacket(self, payload, framNum):
        rtpPacket = RtpPacket()
        rtpPacket.encode(framNum, payload)
        return rtpPacket.getPacket()
    
    def replyRTSP(self, code, seqNum):
        if code == 'OK_200':
            reply = 'RTSP/1.0 200 OK\nCSeq: {}\nSession: {}'.format(seqNum, self.session).encode()
            self.rtsp_socket.send(reply)


if __name__ == '__main__':

    HOST, PORT = '127.0.0.1', 8888 # For local network (server and client seperate on 2 computers)
    # HOST, PORT = '127.0.0.1', 8888 # For one host (on the same computer) 
    rtsp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # RTSP: TCP socket
    rtsp_socket.bind((HOST, PORT))

    # to avoid delay, open live stream before listening
    live_stream_video = LiveStreamVideo()
    live_stream_audio = LiveStreamAudio()
    if not os.path.exists('./cache'):
        os.makedirs('./cache')
    print('RTSP socket listening...')
    rtsp_socket.listen(5)
    while True:
        rtsp_client, addr = rtsp_socket.accept()   # this accept {SockID,tuple object},tuple object = {clinet_addr,intNum}!!!
        ServerWorker(rtsp_client, addr, live_stream_video, live_stream_audio).run()

