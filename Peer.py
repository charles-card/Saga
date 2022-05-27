#!/usr/bin/env python3
import sys
import threading
import time
from CommunicationProtocols import CommunicationProtocol
import socket
from typing import Callable
from abc import ABC, abstractmethod


class Peer(ABC):
    name: str = None
    host: str = None
    port: int = None
    _debug: bool = False

    message_handler: Callable = None

    incoming_socket: socket.socket = None
    comm: CommunicationProtocol = None
    running: bool = False
    connections: dict = {}
    known_peers: dict = {}  # peer_name: (ip, port)

    @abstractmethod
    def send_message(self, name: str, msg: str):
        pass

    @abstractmethod
    def process_message(self, name: str, message: str, handled: bool):
        pass

    @abstractmethod
    def open_connection(self, ip: str, port: int):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def close_connection(self):
        pass

    def get_message_handler(self) -> Callable:
        return self.message_handler

    def set_message_handler(self, message_handler: Callable):
        self.message_handler = message_handler

    def is_connected_to_peer(self, name: str) -> bool:
        """
        Gets connection status to the peer.

        :param name: Name of the peer to check the connection status to.
        :return: True if connection to the peer is open; False otherwise.
        """
        connected = False
        if name in self.connections.keys():
            connected = self.connections[name].is_open()
        return connected

    def is_running(self) -> bool:
        return self.running

    def get_name(self) -> str:
        return self.name

    def is_debug(self) -> bool:
        return self._debug


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
        if name not in self.connections.keys():
            if name in self.known_peers.keys():
                self.open_connection(self.known_peers[name][0], self.known_peers[name][1])
            elif self._debug:
                print('UNKNOWN name {0}'.format(name))

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
        prefix = 'BUILTIN'
        if not handled and message.startswith(prefix):
            handled = True
            args = message.split('-')
            match args[1]:
                case 'PEERLIST':
                    if args[2] == 'REQ':
                        self.send_message(name, self.create_known_peer_list())
                    elif args[2] == 'UPD':
                        peers = args[3].split('>')
                        try:
                            for peer in peers:
                                peer_ = peer.split('@')
                                self.add_peer(peer_[0], peer_[1], int(peer_[2]))
                        except Exception as e:
                            if self._debug:
                                print(e)

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
        peers = self.connections.copy()
        already_connected = False
        for name in peers.keys():
            if peers[name] == (ip, port):
                already_connected = True

        if not already_connected:
            try:
                new_socket = socket.socket()
                new_socket.connect((ip, port))
                comm = CommunicationProtocol(new_socket, (ip, port), self.name, _debug=self._debug)
                comm.establish_encrypted_connection_cs()
                self.connections[comm.get_peer_name()] = comm

                thread = threading.Thread(target=self.connection_listener, args=(comm,))
                #  thread.daemon = True
                thread.start()

                self.add_peer(comm.get_peer_name(), ip, port)

            except ConnectionRefusedError as e:
                if self._debug:
                    print('[FAILED] Unable to connect to \'{0}:{1}\''.format(ip, port))

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

    def start(self):
        """
        Starts a thread to listen to all new incoming connections.
        """
        self.running = True
        thread = threading.Thread(target=self.request_known_peers)
        thread.start()
        self.incoming_connection_listener()

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

    def add_peer(self, peer_name: str, ip: str, port: int):
        known_peers = self.known_peers.copy()
        if peer_name in known_peers.keys():
            if self.known_peers[peer_name] == (ip, port):
                if self._debug:
                    print('[ADD_PEER] PEER [{0}@{1}:{2}] KNOWN'.format(peer_name, ip, port))
            else:
                self.known_peers[peer_name] = (ip, port)
                if self._debug:
                    print('[ADD_PEER] PEER [{0}@{1}:{2}] UPDATED'.format(peer_name, ip, port))
        else:
            self.known_peers[peer_name] = (ip, port)
            if self._debug:
                print('[ADD_PEER] PEER [{0}@{1}:{2}] ADDED'.format(peer_name, ip, port))

    def request_known_peers(self):
        while not self.running:
            pass

        peers = self.known_peers.copy()
        for peer in peers.keys():
            self.send_message(peer, 'BUILTIN-PEERLIST-REQ')

    def create_known_peer_list(self) -> str:
        known_peers = self.known_peers.copy()
        peer_str = 'BUILTIN-PEERLIST-UPD-'
        for peer_name in known_peers.keys():
            peer_str += '{0}@{1}@{2}>'.format(peer_name, *known_peers[peer_name])
        peer_str = peer_str[:len(peer_str) - 1]
        return peer_str




