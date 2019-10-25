# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

# check doc: https://github.com/sipcapture/HEP/tree/master/docs

import socket
import struct
import time

class HEPPacket(object):

    def __init__(self, config, **kwargs):
        self.hep_server = config['hep_server']
        self.hep_port = config['hep_port']
        self.packet_type = "HEP3"

        self.message = {
            "vendor_id": 0,
            "payload_type": 1,
            "capture_id": config['hep_id'],
            "capture_pass": config['hep_pass'],
            "ip_family": 2,
            "protocol": 17,
            "proto_type": 1,
            "src_ip": socket.gethostbyname(kwargs['src_ip']),
            "dst_ip": socket.gethostbyname(kwargs['dst_ip']),
            "src_port": kwargs['src_port'],
            "dst_port": kwargs['dst_port'],
            "payload": None
        }

    def encode(self):
        buffer = bytearray(6)
        header_id = struct.pack_into('4s', buffer, 0, self.packet_type.encode())

        chunks = list()
        chunks.append({'type': 1, 'content': self.message['ip_family'], 'pack': 'B'}) # Proto Family
        chunks.append({'type': 2, 'content': self.message['protocol'], 'pack': 'B'}) # Proto ID
        chunks.append({'type': 3, 'content': socket.inet_aton(self.message['src_ip']), 'pack': '4s'}) # SRC addr
        chunks.append({'type': 4, 'content': socket.inet_aton(self.message['dst_ip']), 'pack': '4s'}) # DST addr
        chunks.append({'type': 7, 'content': self.message['src_port'], 'pack': '!H'}) # SRC port
        chunks.append({'type': 8, 'content': self.message['dst_port'], 'pack': '!H'}) # DST port
        chunks.append({'type': 9, 'content': int(time.time()), 'pack': '!I'}) # Timestamp
        chunks.append({'type': 10, 'content': 0, 'pack': '!I'}) # Microseconds
        chunks.append({'type': 11, 'content': self.message['payload_type'], 'pack': 'B'}) # Payload Type
        chunks.append({'type': 12, 'content': self.message['capture_id'], 'pack': '!I'}) # Capture Agent ID
        chunks.append({'type': 14, 'content': self.message['capture_pass'].encode(), 'pack': '{}s'.format(len(self.message['capture_pass']))}) # Capture agent password
        #chunks.append({'type': 17, 'content': 'call-id'.encode(), 'pack': '{}s'.format(len('call-id'))}) # Correlation ID
        chunks.append({'type': 15, 'content': self.message['payload'].encode(), 'pack': '{}s'.format(len(self.message['payload']))}) # Payload

        for chunk in chunks:
            pack_size = struct.calcsize(chunk['pack']) + 6
            packet = bytearray(pack_size)
            struct.pack_into('!H', packet, 0, self.message['vendor_id'])
            struct.pack_into('!H', packet, 2, chunk['type'])
            struct.pack_into('!H', packet, 4, pack_size)
            struct.pack_into(chunk['pack'], packet, 6, chunk['content'])
            buffer += packet

        total_len = struct.pack_into('!H', buffer, 4, len(buffer))
        return buffer

    def decode(self, payload):
        pass

    def add_payload(self, payload):
        self.message['payload'] = payload

    def send(self, payload):
        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_DGRAM)
        sock.sendto(payload, (self.hep_server, self.hep_port))
        sock.close()

    def __str__(self):
        return str(self.message)
