#!/usr/bin/env python3
from Peer import Peer
import sys
import time

NAME = 'chocy2'
HOST = ''
IN_PORT = 12011


class Client(Peer):

    def __init__(self, name: str, host: str, port: int, _debug: bool = False):
        super().__init__(name, host, port, _debug=_debug)

    def process_message(self, name: str, message: str, _debug: bool = False):
        """
        Processes incoming messages to the Peer

        :param name: Name of the peer the message originated from.
        :param message: Message received from peer.
        :param _debug: If True prints debug information to the console; otherwise no debug information is printed.
        """
        super().process_message(name, message)

        if message == '123':
            self.send_message(name, 'abcdef1')
        elif message == '456':
            self.send_message(name, 'abcdef2')
        elif message == '789':
            self.send_message(name, 'abcdef3')

    def start(self):
        """
        Starts the mainloop for this Peer.
        """
        super().start()

        ip, port = '192.168.1.95', 12010
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
    client = Client(NAME, HOST, IN_PORT, _debug=True)
    try:
        client.start()

    except KeyboardInterrupt as interrupt:
        print()
        client.stop()
        sys.exit(interrupt)

    except OSError as exception:
        print()
        client.stop()
        sys.exit(exception)
