# Video Chat Program with Self-Implemented RTP Protocol
This is the final project for "Introduction to Computer Network" (National Taiwan University). This project aims to implement RTP protocol for video/ audio transmission and devise a video chat program that can transmit video, audio, and transcripts between multiple users.
## Usage
### Video stream
Send a specificied mjpeg. (default: video.mjpeg)
```
# cd to this directory
# First, at one terminal
python Server.py
# Then, at another terminal
python Client_Launcher.py
```
### Live stream
Send the images captured by webcam.
```
# cd to this directory
# First, at one terminal
python Server_livestream.py
# [IMPORTANT!] wait until "RTSP listening..." is printed on the server terminal (wait for the camera open)
# Then, at another terminal
python Client_Launcher.py
```
