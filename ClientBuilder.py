#!/usr/bin/env python3
from Peer import Peer, Client
from Modules import MicrophoneModule, TimeModule, MonitorModule, PeerModule
import argparse
import sys
from typing import Callable

NAME = 'server'
HOST = ''
PORT = 12109


class Singleton(object):
    def __new__(cls, *args, **kwargs):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwargs)
        return it

    def init(self, *args, **kwargs):
        pass


class ClientBuilder(Singleton):  # Decorator Factory Singleton
    _client: Peer = None

    def init(self, name, host, port, _debug):
        self._client = Client(name, host, port, _debug)

    def __add__(self, module: Callable[[Peer], PeerModule]):
        self._client = module(self._client)
        self._client.set_message_handler(self._client.process_message)
        return self

    def start(self):
        self._client.start()

    def stop(self):
        self._client.stop()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This is Saga...')
    parser.add_argument('-n', '--name', help='name of this peer', type=str)
    parser.add_argument('--host', help='interface to listen to for incoming connections', type=str)
    parser.add_argument('-p', '--port', help='the port to accept connections', type=int)
    parser.add_argument('-d', '--debug', help='enables debug mode', action='store_true')
    args_ = parser.parse_args()

    name_ = args_.name if args_.name else NAME
    host_ = args_.host if args_.host else HOST
    port_ = args_.port if args_.port else PORT

    client = ClientBuilder(name_, host_, port_, _debug=args_.debug)
    client = client + MicrophoneModule + TimeModule + MonitorModule
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
