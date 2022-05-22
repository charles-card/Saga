#!/usr/bin/env python3
import sys
import threading
import time

from CommunicationProtocols import CommunicationProtocol
import socket


class Peer(object):

    def __init__(self, name: str, host: str, port: int, _debug: bool = False):
        """
        Initialise Peer Object.

        :param name: Name of this Peer.
        :param host: IP address of the server.
        :param port: Port the peer is listening to.
        :param _debug: If True prints debug information to the console; otherwise no debug information is printed.
        """
        self.name = name
        self.host = host
        self.port = port
        self._debug = _debug

        self.incoming_socket = None
        self.comm = None
        self.running = False
        self.connections = {}

    def send_message(self, name, msg: str):
        """
        Sends message to peer by name.

        :param name: Name of peer to send message to.
        :param msg: Message to be sent to the peer.
        """
        if name in self.connections.keys():
            self.connections[name].send_message(msg)
        else:
            print('Peer {0} is not connected'.format(name))

    def process_message(self, name: str, message: str):
        """
        Intended to be overridden by a child Object to process incoming messages, here to maintain debug printing.

        :param name: Name of peer the message originated from.
        :param message: Message received from peer.
        """

        if self._debug:
            print('[RECEIVED] \"{0}\" FROM {1} '.format(message, name))

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
                    self.process_message(comm.get_peer_name(), message)

        self.connections.pop(comm.get_peer_name())
        sys.exit(0)

    def incoming_connection_listener(self):
        """
        Starts a loop waiting for new incoming connections, opens a new thread to handle each connection.
        """
        self.incoming_socket = socket.socket()
        not_listening = True
        while not_listening:
            try:
                self.incoming_socket.bind(('', self.port))
                self.incoming_socket.listen(10)
                not_listening = False
                if self._debug:
                    print('[AVAILABLE] \'{0}:{1}\''.format('', self.port))

            except socket.error:
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
