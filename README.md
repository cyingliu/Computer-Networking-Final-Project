# Computer-Networking-Final-Project
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
