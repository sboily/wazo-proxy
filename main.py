# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import websockets
import requests
import asyncio

from datetime import datetime
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket
from starlette.requests import Request

from lib.hep import HEPPacket


config = {
    "debug": True,
    "wazo_server": "demo.wazo.community",
    "hep_server": "10.41.0.2",
    "hep_port": 9060,
    "hep_id": "1234",
    "hep_pass": "1234",
    "cors": {
        "origins": [
            "*",
        ]
    }
}

app = FastAPI()
hep_client = HEPPacket(config)

def wazo_log(type, log):
    if config['debug']:
        now = datetime.now()
        dt = now.strftime("%d/%m/%Y %H:%M:%S")
        print("{} Log for {}: {}".format(dt, type, log))

wazo_log('core', 'starting...')

@app.websocket("/api/asterisk/ws")
async def websocket_endpoint(websocket: WebSocket):
    queue_wazo = asyncio.Queue()
    queue_fake = asyncio.Queue()

    await websocket.accept(subprotocol='sip')
    asyncio.create_task(client_ws_sip(queue_wazo, queue_fake))
    await queue_wazo.join()
    await queue_fake.join()

    group1 = asyncio.gather(get_websocket_fake(websocket, queue_fake, True))
    group2 = asyncio.gather(send_websocket_fake(websocket, queue_wazo, True))
    all_groups = await asyncio.gather(group1, group2)

@app.websocket("/api/websocketd")
async def websocket_endpoint(websocket: WebSocket):
    queue_wazo = asyncio.Queue()
    queue_fake = asyncio.Queue()

    token = get_token(websocket.query_params)
    await websocket.accept()
    asyncio.create_task(client_ws_wazo(token, queue_wazo, queue_fake))
    await queue_wazo.join()
    await queue_fake.join()

    group1 = asyncio.gather(get_websocket_fake(websocket, queue_fake))
    group2 = asyncio.gather(send_websocket_fake(websocket, queue_wazo))
    all_groups = await asyncio.gather(group1, group2)

def get_token(url):
    params = dict(x.split('=') for x in str(url).split('&'))
    return params.get('token')

async def get_websocket_fake(websocket, queue, hep=None):
    while True:
        type = 'websocket'
        if hep:
            type = 'sip'
        wazo_log(type, 'Worker to received data from fake websocket')
        data = await websocket.receive_text()
        if hep:
            hep_client.add_payload(data)
            buf = hep_client.encode()
            hep_client.send(buf)
        wazo_log(type, 'Received from websocket fake: {}'.format(data))
        queue.put_nowait(data)

async def send_websocket_fake(websocket, queue, hep=None):
    while True:
        type = 'websocket'
        if hep:
            type = 'sip'
        wazo_log(type, 'Worker to send data to fake websocket')
        data = await queue.get()
        if hep:
            hep_client.add_payload(data)
            buf = hep_client.encode()
            hep_client.send(buf)
        wazo_log(type, 'Received from websocket wazo: {}'.format(data))
        await websocket.send_text(data)
        queue.task_done()

@app.get("/debug")
def debug():
    return {"debug": "ok"}

@app.get("{full_path:path}")
def read_all(full_path: str, request: Request):
    params = None
    if request.query_params:
        params = request.query_params
    r = requests.get('https://{}/{}'.format(config['wazo_server'], full_path), params=params, headers=request.headers)
    try:
        wazo_log('http', r.json())
        return r.json()
    except:
        pass

    return r.content

@app.post("{full_path:path}")
def post_all(full_path: str, item: dict, request: Request):
    r = requests.post('https://{}/{}'.format(config['wazo_server'], full_path), json=item, headers=request.headers)
    try:
        wazo_log('http', r.json())
        return r.json()
    except:
        pass

    return r.content

@app.put("{full_path:path}")
def put_all(full_path: str, item: dict, request: Request):
    r = requests.put('https://{}/{}'.format(config['wazo_server'], full_path), json=item, headers=request.headers)
    try:
        wazo_log('http', r.json())
        return r.json()
    except:
        pass

    return r.content

@app.delete("{full_path:path}")
def delete_all(full_path: str, request: Request):
    r = requests.delete('https://{}/{}'.format(config['wazo_server'], full_path), headers=request.headers)
    return r.text

@app.options("/{full_path:path}")
def options_all(full_path: str):
    r = requests.options('{}/{}'.format(wazo['wazo_server'], full_path))
    return r.text

async def client_ws_sip(queue_wazo, queue_fake):
    uri = "wss://{}/api/asterisk/ws".format(config['wazo_server'])
    async with websockets.connect(uri, subprotocols=["sip"]) as ws:
        group1 = asyncio.gather(get_websocket_wazo(ws, queue_wazo))
        group2 = asyncio.gather(send_websocket_wazo(ws, queue_fake))
        all_groups = await asyncio.gather(group1, group2)

async def client_ws_wazo(token, queue_wazo, queue_fake):
    uri = "wss://{}/api/websocketd/?version=2&token={}".format(config['wazo_server'], token)
    async with websockets.connect(uri) as ws:
        group1 = asyncio.gather(get_websocket_wazo(ws, queue_wazo))
        group2 = asyncio.gather(send_websocket_wazo(ws, queue_fake))
        all_groups = await asyncio.gather(group1, group2)

async def get_websocket_wazo(websocket, queue):
    while True:
        wazo_log('websocket', 'Get data from wazo websocket...')
        data = await websocket.recv()
        wazo_log('websocket', 'Received from wazo: {}'.format(data))
        queue.put_nowait(data)

async def send_websocket_wazo(websocket, queue):
    while True:
        data = await queue.get()
        wazo_log('websocket', 'Received from wazo queue: {}'.format(data))
        await websocket.send(data)
        queue.task_done()

app.add_middleware(
    CORSMiddleware,
    allow_origins=config['cors']['origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
