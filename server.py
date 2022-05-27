#!/usr/bin/env python3
from Peer import Client
from Modules import TimeModule, MicrophoneModule, MonitorModule
import sys
import time
import argparse

NAME = 'server'
HOST = ''
PORT = 12109


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

    server = Client(name_, host_, port_, _debug=args.debug)
    server = TimeModule(server)
    server = MonitorModule(server)
    server = MicrophoneModule(server)
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
