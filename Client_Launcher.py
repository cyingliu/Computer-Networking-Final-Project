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
    client_rtp_port = 6666#int(sys.argv[1])
    filename = "video.mjpeg" #sys.argv[2]

    root = tkinter.Tk()
    root.geometry("1072x603")
    root.configure(background='black')
    app = Client(root, client_rtp_port, filename)
    root.mainloop()