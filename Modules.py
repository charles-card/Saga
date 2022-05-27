#!/usr/bin/env python3
import time
from Peer import Peer
from typing import Callable
import threading


class PeerModule(Peer):
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

    def start(self):
        self._peer.start()

    def stop(self):
        self._peer.stop()

    def close_connection(self):
        self._peer.close_connection()

    def is_connected_to_peer(self, name: str) -> bool:
        return self._peer.is_connected_to_peer(name)

    def is_running(self) -> bool:
        return self._peer.is_running()

    def get_name(self) -> str:
        return self._peer.get_name()

    def get_message_handler(self) -> Callable[[str, str, bool], None]:
        return self._peer.get_message_handler()

    def set_message_handler(self, message_handler: Callable[[str, str, bool], None]):
        self._peer.set_message_handler(message_handler)


class TimeModule(PeerModule):

    def process_message(self, name: str, message: str, handled: bool):
        prefix = 'TIME'
        if not handled and message.startswith(prefix):
            handled = True
            args = message.split('-')
            match args[1]:
                case 'TIMER':
                    length = args[2]
                    unit = args[3]
                    self.create_timer(length, unit)
                    self.send_message(name, 'Timer started for {0} {1}'.format(length, unit))
                case 'ALARM':
                    time_ = args[2]
                    self.create_alarm(time_)
                    self.send_message(name, 'Alarm set for {0}'.format(time_))
                case '789':
                    self.send_message(name, 'zxcvbn3')
                case _:
                    handled = False

        self._peer.process_message(name, message, handled)

    def start(self):
        if not self.get_message_handler():
            self.set_message_handler(self.process_message)
        self._peer.start()

    def create_timer(self, length, unit):
        #  TODO: Implement
        pass

    def create_alarm(self, time_):
        #  TODO: Implement
        pass


class MicrophoneModule(PeerModule):

    def process_message(self, name: str, message: str, handled: bool):
        # Microphones have nothing to output.
        self._peer.process_message(name, message, handled)

    def start(self):
        if not self.get_message_handler():
            self.set_message_handler(self.process_message)

        thread = threading.Thread(target=self.listen)
        thread.start()
        self._peer.start()

    def listen(self):
        peer = ''
        msg = ''
        address = ()
        if self.get_name() == 'server':
            peer = 'chocy1'
            msg = 'MONITORCAMERA-456'
            address = ('192.168.1.95', 12110)
        elif self.get_name() == 'chocy1':
            peer = 'chocy2'
            msg = 'TIME-ALARM-3PM'
            address = ('192.168.1.95', 12111)
        elif self.get_name() == 'chocy2':
            peer = 'server'
            msg = 'TIME-TIMER-3-MINUTES'
            address = ('192.168.1.95', 12109)

        while not self.is_running():
            pass

        while self.is_running():
            if self.is_connected_to_peer(peer):
                self.send_message(peer, msg)
            else:  # here
                try:
                    self.open_connection(address[0], address[1])
                except ConnectionRefusedError:
                    pass
            time.sleep(5)


class MonitorModule(PeerModule):

    def process_message(self, name: str, message: str, handled: bool):
        prefix = 'MONITORCAMERA'
        if not handled and message.startswith(prefix):
            handled = True
            args = message.split('-')
            match args[1]:
                case '123':
                    self.send_message(name, 'zxcvbn1')
                case '456':
                    self.send_message(name, 'I did it.')
                case '789':
                    self.send_message(name, 'zxcvbn3')
                case _:
                    handled = False

        self._peer.process_message(name, message, handled)

    def start(self):
        if not self.get_message_handler():
            self.set_message_handler(self.process_message)
        self._peer.start()
