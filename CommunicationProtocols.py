import random
import socket
import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES
from tinyec.ec import Point
from tinyec import registry


class EncryptionProtocol(object):

    def __init__(self, key, nonce1, nonce2):
        self.key = hashlib.sha256(repr(key).encode()).digest()
        self.prefix = 'SAGA'
        self.nonce_1 = nonce1
        self.nonce_2 = nonce2

    def encrypt(self, raw):
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def mac(self, raw, nonce):
        n_msg = repr(nonce) + raw
        mac = base64.b64encode(hashlib.sha256(n_msg.encode()).digest())
        return mac

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def encode_message(self, raw):
        raw = self.prefix + raw
        enc = self.encrypt(raw)
        mac = self.mac(raw, self.nonce_1)
        self.nonce_1 += 1
        return enc + mac

    def decode_message(self, encoded):
        enc = encoded[:-44]
        mac_received = encoded[-44:]

        message = self.decrypt(enc)
        mac_required = self.mac(message, self.nonce_2)

        mac_correct = mac_required == mac_received
        message_valid = message[:len(self.prefix)] == self.prefix

        if mac_correct and message_valid:
            self.nonce_2 += 1
            return message[len(self.prefix):]
        else:
            raise Exception('Invalid Message.')

    def _pad(self, s):
        return s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)

    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]


class CommunicationProtocol(object):
    def __init__(self, private_key, public_key, ip, port):
        self.my_private_key = private_key
        self.my_public_key = public_key

        self.their_public_key = None
        self.master_key = None

        self.socket = socket.socket()
        self.host = ip
        self.port = port

        self.my_nonce = random.randrange(2 ** 29)
        self.their_nonce = None

        self.encryption_proto = None

        self.log = ''

    def send_hello(self):
        message = repr(self.my_nonce) + ',' + repr(self.my_public_key.x) + ',' + repr(self.my_public_key.y)
        self.socket.send(message.encode())
        self.log += message

    def receive_hello(self):
        response = self.socket.recv(1024)
        nonce, pub_x, pub_y = response.decode().split(',')
        self.their_public_key = Point(registry.get_curve('brainpoolP256r1'), int(pub_x), int(pub_y))
        self.their_nonce = int(nonce)

        self.master_key = self.my_private_key * self.their_public_key
        self.encryption_proto = EncryptionProtocol(self.master_key, self.their_nonce, self.my_nonce)

        self.log += response.decode()

    def send_ack(self):
        self.send_message(self.log)

    def receive_ack(self):
        response = self.receive_message()
        return response

    def open_connection(self):
        self.socket.connect((self.host, self.port))
        self.send_hello()
        self.receive_hello()
        self.send_ack()
        their_log = self.receive_ack()

        if their_log != self.log:
            raise Exception('UnderAttack')

    def wait_connection(self):
        self.socket.bind((self.host, self.port))
        self.socket.listen(10)
        while True:
            self.socket, addr = self.socket.accept()
            self.receive_hello()
            if self.log != '':
                break
        self.send_hello()
        their_log = self.receive_ack()
        self.send_ack()

        if their_log != self.log:
            raise Exception('UnderAttack')

    def send_message(self, message):
        self.socket.send(self.encryption_proto.encode_message(message))

    def receive_message(self):
        response = self.socket.recv(1024)
        message = self.encryption_proto.decode_message(response)
        return message

    def close_connection(self):
        self.socket.close()
