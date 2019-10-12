# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import socket

class HEPPacket(object):

    def __init__(self, config):
        self.hep_server = config['hep_server']
        self.hep_port = config['hep_port']

        ip = "0.0.0.0"

        self.message = {
            "header": {
                "type": "HEP3",
                "payload_type": "SIP",
                "captureId": config['hep_id'],
                "capturePass": config['hep_pass'],
                "ip_family": 2,
                "protocol": 17,
                "proto_type": 1,
                "srcIp": ip,
                "dstIp": ip,
                "srcPort": 0,
                "dstPort": 0,
                "correlation_id": 0
            },
            "payload": None
        }

    def add_payload(self, payload):
        self.message['payload'] = payload

    def send(self):
        bin = ''
        for value in self.message['header']:
           bin += str(value.encode())
        bin += str(self.message['payload'].encode())
        binary = bin.encode()
        sock = socket.socket(socket.AF_INET,
                             socket.SOCK_DGRAM)
        sock.sendto(binary, (self.hep_server, int(self.hep_port)))

    def __str__(self):
        return str(self.message)
