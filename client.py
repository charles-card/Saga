import socket

host = '192.168.1.30'
port = 12009

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((host, port))
    s.sendall(b'Hello World!')

