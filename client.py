#!/usr/bin/env python3
from CommunicationProtocols import CommunicationProtocol
import socket

HOST = '192.168.1.95'
PORT = 12009


class Client(object):

    def __init__(self, name: str, host: str = '192.168.1.95', port: int = 12009):
        """
        Initialise Client Object.

        :param host: IP address of the server.
        :param port: Port the server is listening on.
        """
        self.name = name
        self.host = host
        self.port = port

        self.socket = None
        self.comm = None

    def send_message(self, msg: str):
        """
        Sends message to the server.

        :param msg: Message to be sent to the server.
        :return: Reply received from the server.
        """
        self.comm.send_message(msg)
        reply = self.comm.receive_message()
        self.process_response(reply)
        return reply

    def process_response(self, message: str):
        """
        TODO: Process responses from server

        :param message: Message received in reply from server.
        """
        pass

    def open_connection(self):
        """
        Open connection to the server.
        """
        self.socket = socket.socket()
        self.socket.connect((self.host, self.port))
        self.comm = CommunicationProtocol(self.socket, '', self.name)
        self.comm.establish_encrypted_connection_cs()

    def close_connection(self):
        """
        Closes connection to the server.
        """
        self.comm.close_connection()

    def is_connected_to_server(self):
        """
        Gets connection status to the server.

        :return: True if connection to the server is open; False otherwise.
        """
        return self.comm.is_open()


if __name__ == '__main__':
    client_name = input('What is the name of your client?: ')
    client = Client(client_name)
    client.open_connection()
    while client.is_connected_to_server():
        txt = input('Message for server: ')
        reply = client.send_message(txt)
        print('Response from Server: {0}'.format(reply[0]))
