#!/usr/bin/env python3
import sys
from CommunicationProtocols import CommunicationProtocol
import socket
import threading


class Server(object):

    def __init__(self, host='', port=12009, file_prefix='server-'):
        self.host = host
        self.port = port
        self.file_prefix = file_prefix

        self.socket = None

        # self.states = ['Waiting for Hello', 'Waiting for ACK', 'Waiting for Message']
        self.client_threads = []

    def start(self):
        self.socket = socket.socket()
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
        except socket.error as e:
            print(str(e))
            sys.exit(e)

        while True:
            client, addr = self.socket.accept()
            print('Thread {0}'.format(str(len(threading.enumerate()))))
            thread = threading.Thread(target=self.client_connection, args=(client,))
            thread.start()

    def process_message(self, message):
        return 'blah'

    def close_connection(self):
        self.socket.close()

    def client_connection(self, connection):
        comm = CommunicationProtocol(connection, file_prefix=self.file_prefix)
        comm.establish_encrypted_connection_ss()
        while comm.is_open():
            message = comm.receive_message()
            if message[0] != 'END':
                reply = self.process_message(message)
                comm.send_message(reply)
                print('Received: {0}'.format(message))
                print('Response: {0}'.format(reply))
        sys.exit(0)


if __name__ == '__main__':
    server = Server()
    try:
        server.start()

    except KeyboardInterrupt as interrupt:
        server.close_connection()
        sys.exit(interrupt)

    except OSError as exception:
        server.close_connection()
        sys.exit(exception)
