import socket
import struct
import select
from core.aochat.server_packets import ServerPacket, LoginOK
from core.aochat.client_packets import LoginRequest, LoginSelect
from tools.logger import Logger
from core.aochat.crypt import generate_login_key


class Bot:
    def __init__(self):
        self.socket = None
        self.char_id = None
        self.char_name = None
        self.logger = Logger("Mangopie")

    def connect(self, host, port):
        self.logger.info("Connecting to %s:%d" % (host, port))
        self.socket = socket.create_connection((host, port), 10)

    def disconnect(self):
        if self.socket:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.socket = None

    def login(self, username, password, character):
        character = character.capitalize()

        # read seed packet
        self.logger.info(("Logging in as %s" % character))
        seed_packet = self.read_packet(10)
        seed = seed_packet.seed

        # send back challenge
        key = generate_login_key(seed, username, password)
        login_request_packet = LoginRequest(0, username, key)
        self.send_packet(login_request_packet)

        # read character list
        character_list_packet = self.read_packet()
        index = character_list_packet.names.index(character)

        # select character
        self.char_id = character_list_packet.character_ids[index]
        self.char_name = character_list_packet.names[index]
        login_select_packet = LoginSelect(self.char_id)
        self.send_packet(login_select_packet)

        # wait for OK
        packet = self.read_packet()
        if packet.id == LoginOK.id:
            self.logger.info("Connected!")
            return True
        else:
            self.logger.error("Error logging in: %s" % packet.message)
            return False

    def read_packet(self, time=1):
        """
        Wait for packet from server.
        """

        read, write, error = select.select([self.socket], [], [], time)
        if not read:
            return None
        else:
            # Read data from server
            head = self.read_bytes(4)
            packet_type, packet_length = struct.unpack(">2H", head)
            data = self.read_bytes(packet_length)

            packet = ServerPacket.get_instance(packet_type, data)
            return packet

    def send_packet(self, packet):
        data = packet.to_bytes()
        data = struct.pack(">2H", packet.id, len(data)) + data

        self.write_bytes(data)

    def read_bytes(self, num_bytes):
        data = bytes()

        while num_bytes > 0:
            chunk = self.socket.recv(num_bytes)

            if len(chunk) == 0:
                raise EOFError

            num_bytes -= len(chunk)
            data = data + chunk

        return data

    def write_bytes(self, data):
        num_bytes = len(data)

        while num_bytes > 0:
            sent = self.socket.send(data)

            if sent == 0:
                raise EOFError

            data = data[sent:]
            num_bytes -= sent
