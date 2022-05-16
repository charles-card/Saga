import socket

s = socket.socket()
host = '127.0.0.1'
port = 12009

s.bind((host, port))

s.listen(10)

while True:
    c, addr = s.accept()
    print('Connection established {0}'.format(addr))
    content = c.recv(1024).decode()
    if not content:
        break
    print(content)
