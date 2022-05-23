#!/usr/bin/env python3
from Peer import Client
import sys
import time
import argparse

NAME = 'chocy2'
HOST = ''
PORT = 12111


class Chocy(Client):

    def __init__(self, name: str, host: str, port: int, _debug: bool = False):
        super().__init__(name, host, port, _debug=_debug)
        self.message_handler = self.process_message

    def process_message(self, name: str, message: str, handled: bool):
        """
        Processes incoming messages to the Peer

        :param name: Name of the peer the message originated from.
        :param message: Message received from peer.
        :param handled: If True message was handled; False otherwise.
        """

        if message == '123':
            self.send_message(name, 'abcdef1')
            handled = True
        elif message == '456':
            self.send_message(name, 'abcdef2')
            handled = True
        elif message == '789':
            self.send_message(name, 'abcdef3')
            handled = True

        super().process_message(name, message, handled)

    def start(self, message_handler):
        """
        Starts the mainloop for this Peer.
        """
        if not message_handler:
            message_handler = self.process_message
        super().start(message_handler)

        ip, port = '192.168.1.95', 12110
        peer = 'chocy1'
        while self.running:
            time.sleep(1)
            if self.is_connected_to_peer(peer):
                self.send_message(peer, '789')
            else:
                try:
                    self.open_connection(ip, port)
                except ConnectionRefusedError:
                    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This is Saga...')
    parser.add_argument('-n', '--name', help='name of this peer', type=str)
    parser.add_argument('--host', help='interface to listen to for incoming connections', type=str)
    parser.add_argument('-p', '--port', help='the port to accept connections', type=int)
    parser.add_argument('-d', '--debug', help='enables debug mode', action='store_true')
    args = parser.parse_args()

    name_ = args.name if args.name else NAME
    host_ = args.host if args.host else HOST
    port_ = args.port if args.port else PORT

    client = Chocy(name_, host_, port_, _debug=args.debug)
    try:
        client.start(None)

    except KeyboardInterrupt as interrupt:
        print()
        client.stop()
        sys.exit(interrupt)

    except OSError as exception:
        print()
        client.stop()
        sys.exit(exception)
