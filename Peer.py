#!/usr/bin/env python3
import sys
import threading
import time

from CommunicationProtocols import CommunicationProtocol
import socket
from typing import Callable


class Peer(object):
    name: str = None
    host: str = None
    port: int = None
    _debug: bool = False

    message_handler: Callable = None

    incoming_socket: socket.socket = None
    comm: CommunicationProtocol = None
    running: bool = False
    connections: dict = {}

    def send_message(self, name: str, msg: str):
        pass

    def process_message(self, name: str, message: str, handled: bool):
        pass

    def open_connection(self, ip: str, port: int):
        pass

    def connection_listener(self, comm: CommunicationProtocol):
        pass

    def incoming_connection_listener(self):
        pass

    def start(self, message_handler):
        pass

    def stop(self):
        pass

    def close_connection(self):
        pass

    def is_connected_to_peer(self, name: str):
        pass


class PeerDecorator(Peer):
    _peer: Peer = None

    def __init__(self, peer: Peer):
        self._peer = peer

    def peer(self) -> Peer:
        return self._peer

    def send_message(self, name: str, msg: str):
        self._peer.send_message(name, msg)

    def process_message(self, name: str, message: str, handled: bool):
        self._peer.process_message(name, message, handled)

    def open_connection(self, ip: str, port: int):
        self._peer.open_connection(ip, port)

    def connection_listener(self, comm: CommunicationProtocol):
        self._peer.connection_listener(comm)

    def incoming_connection_listener(self):
        self._peer.incoming_connection_listener()

    def start(self, message_handler):
        self._peer.start(message_handler)

    def stop(self):
        self._peer.stop()

    def close_connection(self):
        self._peer.close_connection()

    def is_connected_to_peer(self, name: str):
        self._peer.is_connected_to_peer(name)


class MicrophoneDecorator(PeerDecorator):

    def process_message(self, name: str, message: str, handled: bool):
        self._peer.process_message(name, message, handled)

    def start(self, message_handler):
        if not message_handler:
            message_handler = self.process_message
        self._peer.start(message_handler)


class MonitorDecorator(PeerDecorator):

    def process_message(self, name: str, message: str, handled: bool):
        prefix = 'MONITORCAMERA'
        if not handled and message.startswith(prefix):
            handled = True
            args = message.split('-')
            match args[1]:
                case '123':
                    self.send_message(name, 'zxcvbn1')
                case '456':
                    self.send_message(name, 'zxcvbn2')
                case '789':
                    self.send_message(name, 'zxcvbn3')
                case _:
                    handled = False

        self._peer.process_message(name, message, handled)

    def start(self, message_handler):
        if not message_handler:
            message_handler = self.process_message
        self._peer.start(message_handler)


class Client(Peer):

    def __init__(self, name: str, host: str, port: int, _debug: bool = False):
        """
        Initialise Client Object.

        :param name: Name of this Peer.
        :param host: IP address of the server.
        :param port: Port the peer is listening to.
        :param _debug: If True prints debug information to the console; otherwise no debug information is printed.
        """
        self.name = name
        self.host = host
        self.port = port
        self._debug = _debug

    def send_message(self, name: str, msg: str):
        """
        Sends message to peer by name.

        :param name: Name of peer to send message to.
        :param msg: Message to be sent to the peer.
        """
        if name in self.connections.keys():
            self.connections[name].send_message(msg)
        else:
            print('Peer {0} is not connected'.format(name))

    def process_message(self, name: str, message: str, handled: bool):
        """
        Intended to be overridden by a child Object to process incoming messages, here to maintain debug printing.

        :param name: Name of peer the message originated from.
        :param message: Message received from peer.
        :param handled: True if the message has been handled; False otherwise.
        """

        if self._debug:
            if handled:
                print('[RECEIVED] \"{0}\" FROM {1} '.format(message, name))
            else:
                print('[RECEIVED UNKNOWN] \"{0}\" FROM {1} '.format(message, name))

    def open_connection(self, ip: str, port: int):
        """
        Open connection to the server.

        :param ip: IP address to open a connection to.
        :param port: Port to open a connection on.
        """
        try:
            new_socket = socket.socket()
            new_socket.connect((ip, port))
            comm = CommunicationProtocol(new_socket, (ip, port), self.name, _debug=self._debug)
            comm.establish_encrypted_connection_cs()
            self.connections[comm.get_peer_name()] = comm

            thread = threading.Thread(target=self.connection_listener, args=(comm,))
            #  thread.daemon = True
            thread.start()
        except ConnectionRefusedError as e:
            if self._debug:
                print('[FAILED] Unable to connect to \'{0}:{1}\''.format(ip, port))
            raise ConnectionRefusedError(e)

    def connection_listener(self, comm: CommunicationProtocol):
        """
        Called when a new connection is made to the client.

        :param comm: CommunicationProtocol object representing the connection to the client.
        """
        while comm.is_open() and self.running:
            messages = comm.receive_message()
            if messages:
                for message in messages:
                    self.message_handler(comm.get_peer_name(), message, False)

        self.connections.pop(comm.get_peer_name())
        sys.exit(0)

    def incoming_connection_listener(self):
        """
        Starts a loop waiting for new incoming connections, opens a new thread to handle each connection.
        """
        self.incoming_socket = socket.socket()
        self.incoming_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        not_listening = True
        while not_listening:
            try:
                self.incoming_socket.bind(('', self.port))
                self.incoming_socket.listen(10)
                not_listening = False
                if self._debug:
                    print('[AVAILABLE] \'{0}:{1}\''.format('', self.port))

            except socket.error as e:
                print(str(e))
                if self._debug:
                    print('[UNAVAILABLE] \'{0}:{1}\' RETRYING in 1 second'.format('', self.port))
                time.sleep(1)

            except KeyboardInterrupt as interrupt:
                print()
                self.stop()
                sys.exit(interrupt)

        while self.running:
            peer, addr = self.incoming_socket.accept()
            try:
                comm = CommunicationProtocol(peer, addr, self.name, file_prefix='{0}-'.format(self.name),
                                             _debug=self._debug)
                comm.establish_encrypted_connection_ss()
                self.connections[comm.get_peer_name()] = comm

                thread = threading.Thread(target=self.connection_listener, args=(comm,))
                #  thread.daemon = True
                thread.start()
            except Exception as e:
                print(str(e))

    def start(self, message_handler):
        """
        Starts a thread to listen to all new incoming connections.
        """
        self.message_handler = message_handler
        self.running = True

        thread = threading.Thread(target=self.incoming_connection_listener)
        #  thread.daemon = True
        thread.start()

    def stop(self):
        """
        Stops the peer safely.
        """
        incoming_connections = self.connections.copy()
        for name in incoming_connections:
            self.connections[name].close_connection()

        self.running = False
        self.incoming_socket.close()
        if self._debug:
            print('Stopped peer.')

    def close_connection(self):
        """
        Closes connection to the server.
        """
        self.comm.close_connection()

    def is_connected_to_peer(self, name: str):
        """
        Gets connection status to the peer.

        :param name: Name of the peer to check the connection status to.
        :return: True if connection to the peer is open; False otherwise.
        """
        connected = False
        if name in self.connections.keys():
            connected = self.connections[name].is_open()

        return connected



