#!/usr/bin/env python3
from CommunicationProtocols import CommunicationProtocol
from tinyec import registry
import secrets

HOST = '192.168.1.30'
PORT = 12009


if __name__ == '__main__':
    curve = registry.get_curve('brainpoolP256r1')

    private_key = secrets.randbelow(curve.field.n)
    public_key = private_key * curve.g

    connection = CommunicationProtocol(private_key, public_key, HOST, PORT)

    connection.wait_connection()
    print(connection.receive_message())
    connection.close_connection()
