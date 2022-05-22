#!/usr/bin/env python3
import sys
from CommunicationProtocols import CommunicationProtocol
import socket
import threading


class Server(object):

    def __init__(self, host: str = '', port: int = 12009):
        """
        Initialise Server object

        :param host: IP address of the server.
        :param port: Port for the server to listen on.
        """
        self.host = host
        self.port = port

        self.socket = None

        # self.states = ['Waiting for Hello', 'Waiting for ACK', 'Waiting for Message']
        self.processes = []
        self.connections = []
        self.running = False

    def start(self):
        """
        Starts a loop waiting for new incoming connections, opens a new daemon thread to handle each connection.
        """
        self.running = True
        self.socket = socket.socket()
        try:
            self.socket.bind((self.host, self.port))
            self.socket.listen(10)
        except socket.error as e:
            print(str(e))
            sys.exit(e)

        while self.running:
            client, addr = self.socket.accept()
            try:
                comm = CommunicationProtocol(client, addr, 'server', file_prefix='server-')
                comm.establish_encrypted_connection_ss()
                self.connections.append(comm)

                thread = threading.Thread(target=self.client_connection, args=(comm, ))
                thread.daemon = True
                thread.start()
            except Exception as e:
                print(e)

    def stop(self):
        """
        Stops the main loop.
        """
        for comm in self.connections:
            comm.close_connection()
        self.running = False
        self.socket.close()
        print('Stopped server.')

    def process_message(self, message: str, address: str, peer_name, _debug: bool = False) -> str:
        """
        Processes a message received by the server.

        :param peer_name: Name of peer.
        :param message: String message sent to the server from the client
        :param address: Address of the client that sent the message
        :param _debug: If True prints debug information to console
        :return:
        """
        reply = 'Blah'

        if _debug:
            print('RECEIVED: \"{0}\" FROM {1}@{2}:{3} '.format(message, peer_name, address[0], address[1]))
            print('RESPONSE: {0}'.format(reply))

        return reply

    def client_connection(self, comm: CommunicationProtocol):
        """
        Called when a new connection is made to the server, handles receiving data packets

        :param comm: socket object representing the connection to the client
        """
        while comm.is_open() & self.running:
            messages = comm.receive_message()
            if messages[0] != 'END':
                for message in messages:
                    reply = self.process_message(message, comm.get_address(), comm.get_peer_name(), _debug=False)
                    comm.send_message(reply)
        print('Thread closing')
        sys.exit(0)


if __name__ == '__main__':
    server = Server()
    try:
        server.start()

    except KeyboardInterrupt as interrupt:
        print()
        server.stop()
        sys.exit(interrupt)

    except OSError as exception:
        print()
        server.stop()
        sys.exit(exception)
