#!/usr/bin/env python3
import sys
from CommunicationProtocols import CommunicationProtocol
import socket
import multiprocessing


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
            process = multiprocessing.Process(target=self.client_connection, args=(client, addr, ))
            self.processes.append(process)
            process.start()

    def stop(self):
        """
        Stops the main loop.
        """
        self.running = False
        for process in multiprocessing.active_children():
            process.terminate()
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        print('Stopped.')

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

    def close_connection(self):
        """
        Closes the socket receiving and sending packets.
        """
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        print('Closed Socket')

    def client_connection(self, connection: socket.socket, addr):
        """
        Called when a new connection is made to the server, handles receiving data packets

        :param connection: socket object representing the connection to the client
        :param addr: iPv4 address of incoming connection
        """
        comm = CommunicationProtocol(connection, addr, 'server', file_prefix='server-')
        comm.establish_encrypted_connection_ss()
        while comm.is_open() & self.running:
            messages = comm.receive_message()
            if messages[0] != 'END':
                for message in messages:
                    reply = self.process_message(message, comm.get_address(), comm.get_peer_name(), _debug=True)
                    comm.send_message(reply)
        print('Thread closing')
        sys.exit(0)


if __name__ == '__main__':
    server = Server()
    try:
        server.start()

    except KeyboardInterrupt as interrupt:
        server.stop()
        #server.close_connection()
        sys.exit(interrupt)

    except OSError as exception:
        server.stop()
        #server.close_connection()
        sys.exit(exception)
