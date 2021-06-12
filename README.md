# Python socket chat

[Version of this project without 3rd party tcl styles](https://github.com/makubas/python-scoket-chat-nostyles)

Project made by me while learning about sockets. The way how it works, is that you need to
run a server (ONLY 1 AT ONCE) and clients (you can have multiple on one computer). 

To run this project:

`git clone https://github.com/makubas/python-socket-chat`

`cd python-socket-chat`

`python server.py`

Now, to run clients, you need to open a new command line window in the project folder and 
run `python client.py`. To connect with server, enter your username and server address which
will appear in server window. For example: `10.0.0.100:5050`. 5050 is a port defined in config.py.
If it won't work, change `SERVER` variable in config.py to your own computer private ip address.
