#!/usr/bin/env python3
from CommunicationProtocols import CommunicationProtocol
import socket

HOST = '192.168.1.95'
PORT = 12009


class Client(object):

    def __init__(self, host='192.168.1.95', port=12009, file_prefix='client-'):
        self.host = host
        self.port = port
        self.file_prefix = file_prefix

        self.socket = None
        self.comm = None

    def send_message(self, msg):
        self.comm.send_message(msg)
        reply = self.comm.receive_message()
        self.process_response(reply)

    def process_response(self, message):
        print(message)

    def open_connection(self):
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))
        self.comm = CommunicationProtocol(self.socket)
        self.comm.establish_encrypted_connection_cs()

    def close_connection(self):
        self.comm.close_connection()


if __name__ == '__main__':
    client = Client()
    client.open_connection()
    client.send_message('yeet')
    client.close_connection()
