import sys
import tkinter
from Client import Client
import os

def cleanCache():
    allfiles = os.listdir()
    for file in allfiles:
        if file[:6] == "cache-":os.remove(file)

if __name__ == '__main__':

    cleanCache()
    client_rtp_port_video = 6666# int(sys.argv[1])
    client_rtp_port_audio = 7777# int(sys.argv[1])
    client_rtp_port_word = 5555
    filename = "video.mjpeg" #sys.argv[2]

    root = tkinter.Tk()
    root.geometry("1072x603")
    root.configure(background='black')
    app = Client(root, client_rtp_port_video, client_rtp_port_audio, client_rtp_port_word, filename)
    root.mainloop()
