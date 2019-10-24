# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

# check doc: https://github.com/sipcapture/HEP/tree/master/docs

import socket
import struct

class HEPPacket(object):

    def __init__(self, config):
        self.hep_server = config['hep_server']
        self.hep_port = config['hep_port']
        self.packet_type = "HEP3"

        ip = "0.0.0.0"

        self.message = {
            "vendor_id": '0',
            "payload_type": "SIP",
            "capture_id": config['hep_id'],
            "capture_pass": config['hep_pass'],
            "ip_family": '2',
            "protocol": '17',
            "proto_type": '1',
            "src_ip": ip,
            "dst_ip": ip,
            "src_port": '',
            "dst_port": '',
            "correlation_id": '',
            "payload": ''
        }

    def encode(self):
        buffer = bytearray(6)
        header_id = struct.pack_into('4s', buffer, 0, self.packet_type.encode())

        chunks = list()
        chunks.append({'type': 1, 'content': 2, 'pack': 'B'}) # Proto Family
        chunks.append({'type': 2, 'content': 17, 'pack': 'B'}) # Proto ID (udp)
        chunks.append({'type': 3, 'content': socket.inet_aton('127.0.0.2'), 'pack': '4s'}) # SRC addr
        chunks.append({'type': 4, 'content': socket.inet_aton('127.0.0.1'), 'pack': '4s'}) # DST addr
        chunks.append({'type': 7, 'content': 5061, 'pack': '>H'}) # SRC port
        chunks.append({'type': 8, 'content': 5060, 'pack': '>H'}) # DST port
        chunks.append({'type': 9, 'content': 1571958119, 'pack': '>I'}) # Timestamp
        chunks.append({'type': 10, 'content': 0, 'pack': '>I'}) # Microseconds
        chunks.append({'type': 11, 'content': 1, 'pack': 'B'}) # Payload Type (1 = SIP)
        chunks.append({'type': 12, 'content': int(self.message['capture_id']), 'pack': '>I'}) # Capture Agent ID
        chunks.append({'type': 14, 'content': self.message['capture_pass'].encode(), 'pack': '{}s'.format(len(self.message['capture_pass']))}) # Capture agent password
        chunks.append({'type': 15, 'content': self.message['payload'].encode(), 'pack': '{}s'.format(len(self.message['payload']))}) # Payload

        for chunk in chunks:
            pack_size = struct.calcsize(chunk['pack'])
            packet = bytearray(pack_size+6)
            struct.pack_into('>H', packet, 0, int(self.message['vendor_id']))
            struct.pack_into('>H', packet, 2, chunk['type'])
            struct.pack_into('>H', packet, 4, pack_size+6)
            struct.pack_into(chunk['pack'], packet, 6, chunk['content'])
            buffer += packet

        total_len = struct.pack_into('>H', buffer, 4, len(buffer))
        return buffer

    def decode(self, payload):
        pass

    def add_payload(self, payload):
        self.message['payload'] = payload

    def send(self, payload):
        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_DGRAM)
        sock.sendto(payload, (self.hep_server, int(self.hep_port)))
        sock.close()

    def __str__(self):
        return str(self.message)
