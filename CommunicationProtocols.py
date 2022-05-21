import random
import base64
import hashlib
import socket

from Crypto import Random
from Crypto.Cipher import AES
from tinyec.ec import Point
from tinyec import registry
import secrets


class EncryptionProtocol(object):

    def __init__(self, key, nonce1, nonce2):
        """
        Initialise EncryptionProtocol Object.

        :param key: Master Key for communication between two peers.
        :param nonce1: Number-Used-Once, used for encryption to prevent replay attacks.
        :param nonce2: Number-Used-Once, used for decryption to prevent replay attacks.
        """
        self.key = hashlib.sha256(repr(key).encode()).digest()
        self.prefix = 'SAGA'
        self.nonce_1 = nonce1
        self.nonce_2 = nonce2

    def encrypt(self, raw):
        """
        Encrypts a plaintext into ciphertext under the provided key.

        :param raw: Plaintext to be encrypted.
        :return: Ciphertext generated from the plaintext.
        """
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    @staticmethod
    def mac(raw, nonce):
        """
        Creates a Message-Authentication-Code.

        :param raw: Plaintext to be hashed.
        :param nonce: Number-Used-Once, prevents replay attacks.
        :return: The sha256 hash of the plaintext and nonce.
        """
        n_msg = repr(nonce) + raw
        mac = base64.b64encode(hashlib.sha256(n_msg.encode()).digest())
        return mac

    def decrypt(self, enc):
        """
        Decrypts the ciphertext and generates the original plaintext.

        :param enc: The encrypted message.
        :return: The decrypted message.
        """
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def encode_message(self, raw):
        """
        Encodes the plaintext, encrypt(raw) + mac(raw+nonce)

        :param raw: Plaintext to be encoded.
        :return: Ciphertext
        """
        raw = self.prefix + raw
        enc = self.encrypt(raw)
        mac = self.mac(raw, self.nonce_1)
        self.nonce_1 += 1
        return enc + mac

    def decode_message(self, encoded):
        """
        Decodes ciphertext into plaintext and validates the origin.

        :param encoded: Ciphertext to be decrypted.
        :return: Plaintext of original message.
        """
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

    @staticmethod
    def _pad(s):
        """
        Adds padding to plaintext to match block_size for encryption.

        :param s: Plaintext.
        :return: Padded plaintext.
        """
        return s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)

    @staticmethod
    def _unpad(s):
        """
        Removes padding from a padded plaintext.

        :param s: Padded plaintext.
        :return: Plaintext.
        """
        return s[:-ord(s[len(s) - 1:])]


class CommunicationProtocol(object):
    def __init__(self, connection: socket.socket, address: str, name: str,
                 private_key=None, public_key=None, file_prefix='', _eom='\x00'):
        """
        Initialise CommunicationProtocol.

        :param connection: Socket object for the connection between two peers.
        :param private_key: Private key of this client.
        :param public_key: Public key of this client.
        :param file_prefix: File prefix for saving and loading keys.
        :param _eom: End-Of-Message Character used to separate different messages from one another.
        """
        self.my_name = name
        self.peer_name = None
        self.key_prefix = file_prefix
        self.address = address
        self.eom = _eom  # End-of-Message character

        self.connection = connection

        if private_key is not None and public_key is not None:
            self.my_private_key = private_key
            self.my_public_key = public_key
        elif private_key is None and public_key is None:
            self.my_private_key, self.my_public_key = self.generate_keys()
        else:
            raise Exception('Must provide either both keys or no keys.')

        self.their_public_key = None
        self.master_key = None
        self.my_nonce = random.randrange(2 ** 29)  # Prevent replay attacks
        self.open = True
        self.encryption_proto = None
        self.buffer = b''
        self.log = ''

    @staticmethod
    def generate_keys():
        """
        Generates a random key-pair.

        :return: Tuple of generated Private and Public keys.
        """
        curve = registry.get_curve('brainpoolP256r1')
        private_key = secrets.randbelow(curve.field.n)
        public_key = private_key * curve.g

        return private_key, public_key

    @staticmethod
    def generate_nonce():
        """
        Generates a random nonce.

        :return: A random nonce.
        """
        return random.randrange(2 ** 29)

    def store_local_keys(self):
        pass

    def store_peer_keys(self):
        pass

    def send_hello(self):  # TODO: Revisit this later, sending nonce as plaintext seems irresponsible.
        """
        Sends a hello message to a peer.
        Hello - my_nonce, public_key.x, public_key.y
        """
        message = ','.join((repr(self.my_nonce), repr(self.my_public_key.x), repr(self.my_public_key.y)))
        self.connection.send(message.encode())
        self.log += message

    def receive_hello(self):
        """
        Receives a hello message from peer.
        Hello - their_nonce, public_key.x, public_key.y
        Stores their nonce and public key.
        Uses their public key and our private key to generate a master key.
        """
        response = self.connection.recv(1024)
        nonce, pub_x, pub_y = response.decode().split(',')
        self.their_public_key = Point(registry.get_curve('brainpoolP256r1'), int(pub_x), int(pub_y))
        their_nonce = int(nonce)

        self.master_key = self.my_private_key * self.their_public_key
        self.encryption_proto = EncryptionProtocol(self.master_key, their_nonce, self.my_nonce)

        self.log += response.decode()

    def send_ack(self):
        """
        Sends entire message log to peer.
        """
        ack = ','.join((self.log, self.my_name))
        self.connection.send(self.encryption_proto.encode_message(ack))

    def receive_ack(self):
        """
        Receives the entire message log of the peer.

        :return: The peers log.
        """
        bytes_ack = self.connection.recv(1024)
        ack = self.encryption_proto.decode_message(bytes_ack)
        ack = ack.split(',')
        ack = [','.join(ack[:-1]), ack[-1]]
        return ack

    def send_message(self, message):
        """
        Encrypts plaintext and sends the ciphertext to the peer.

        :param message: Plaintext message to send to the peer
        """
        message = self.encryption_proto.encode_message(message)
        self.connection.send(message + bytes(self.eom, 'utf-8'))

    def buffer_split_received(self, received):
        """
        Splits and buffers messages as needed.
        If a message is too long for the size of the socket buffer, the socket buffer is emptied into a buffer variable.
        If multiple messages are received, the messages are split up and returned in a list.
        Does both if multiple messages are sent where at least one message is shorter than the socket buffer size.

        :param received: Bytes received by socket.
        :return: List of messages received.
        """
        received = received.decode('utf-8')  # Convert received ciphertext to utf-8
        messages = []
        x = 0  # Start of message position
        for i in range(0, len(received), 1):
            if received[i] == self.eom:
                messages.append(bytes(received[x:i], 'utf-8'))
                x = i+1

        if len(messages) > 0:  # If an eom was received, complete the first message from buffer
            messages[0] = self.buffer + messages[0]
            self.buffer = b''

        self.buffer = self.buffer + bytes(received[x:], 'utf-8')  # Update Buffer

        return messages  # return List of messages received

    def receive_message(self):
        """
        Receive a message from the peer.

        :return: The message receives.
        """
        try:
            byte_string = self.connection.recv(1024)

            if len(byte_string) == 0:
                self.open = False
                return ['END']

            responses = self.buffer_split_received(byte_string)
            messages = []

            if responses:
                for response in responses:
                    messages.append(self.encryption_proto.decode_message(response))
            return messages

        except ConnectionError:
            self.open = False
            return ['END']

    def close_connection(self):
        """
        Closes the connection to the peer.
        """
        self.connection.close()
        self.open = False

    def is_open(self):
        """
        Checks if the connection to the peer is still open.

        :return: True if connection is open; False otherwise.
        """
        return self.open  # return True if connection is open, False otherwise.

    def get_eom(self):
        """
        Gets the End-Of-Message character

        :return: End-Of-Message character
        """
        return self.eom  # return End-of-Message character

    def establish_encrypted_connection_ss(self):
        """
        Establishes an encrypted connection from the Server-Side.
        """
        self.receive_hello()
        self.send_hello()
        ack = self.receive_ack()
        self.peer_name = ack[1]
        self.send_ack()
        if ack[0] != self.log:
            raise Exception('Under Attack')

    def establish_encrypted_connection_cs(self):
        """
        Establishes an encrypted connection from the Client-Side.
        """
        self.open = True
        self.send_hello()
        self.receive_hello()
        self.send_ack()
        ack = self.receive_ack()
        self.peer_name = ack[1]
        if ack[0] != self.log:
            raise Exception('UnderAttack')

    def get_peer_name(self):
        """
        Gets name of peer.

        :return: Name of peer.
        """
        return self.peer_name

    def get_address(self):
        """
        Gets address of peer

        :return: Name of peer.
        """
        return self.address
