# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

# check doc: https://github.com/sipcapture/HEP/tree/master/docs

import socket
import struct

class HEPPacket(object):

    def __init__(self, config):
        self.hep_server = config['hep_server']
        self.hep_port = config['hep_port']

        ip = "0.0.0.0"

        self.message = {
            "type": "HEP3",
            "vendor_id": '4',
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

    def add_payload(self, payload):
        self.message['payload'] = payload

    def send(self):
        size = sum([len(x) for x in self.message.values()])
        buffer = bytearray(15)
        header_id = struct.pack_into('4s', buffer, 0, self.message['type'].encode())
        total_len = struct.pack_into('h', buffer, 4, size)

        chunks = list()
        chunks.append({'type': 1, 'content': 2, 'pack': 'L'}) # Proto Family
        chunks.append({'type': 2, 'content': 17, 'pack': 'L'}) # Proto ID (udp)
        chunks.append({'type': 3, 'content': '0.0.0.0'.encode(), 'pack': '4s'}) # SRC addr
        chunks.append({'type': 4, 'content': '0.0.0.0'.encode(), 'pack': '4s'}) # DST addr
        chunks.append({'type': 7, 'content': 5060, 'pack': 'I'}) # SRC port
        chunks.append({'type': 8, 'content': 5060, 'pack': 'I'}) # DST port
        chunks.append({'type': 9, 'content': 1509467455, 'pack': 'I'}) # Timestamp
        chunks.append({'type': 10, 'content': 1509467455, 'pack': 'I'}) # Microseconds
        chunks.append({'type': 11, 'content': 100, 'pack': 'I'}) # Payload Type (100 = plain text)
        chunks.append({'type': 12, 'content': 0, 'pack': 'I'}) # Capture Agent ID
        chunks.append({'type': 17, 'content': 'callid'.encode(), 'pack': '4s'}) # Call-ID
        chunks.append({'type': 15, 'content': self.message['payload'].encode(), 'pack': '{}s'.format(len(self.message['payload']))}) # Payload

        buffers = list()
        buf = 0
        for chunk in chunks:
            pack_size = struct.calcsize(chunk['pack'])
            buffers.append(bytearray(6+pack_size))
            struct.pack_into('>I', buffers[buf], 0, int(self.message['vendor_id']))
            struct.pack_into('I', buffers[buf], 4, chunk['type'])
            struct.pack_into('{}'.format(chunk['pack']), buffers[buf], 6, chunk['content'])
            buffer += buffers[buf]
            buf += 1

        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_DGRAM)
        sock.sendto(buffer, (self.hep_server, int(self.hep_port)))
        sock.close()

    def __str__(self):
        return str(self.message)
