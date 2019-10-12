import websockets
import requests
import asyncio

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.websockets import WebSocket
from starlette.requests import Request


app = FastAPI()
server = 'demo.wazo.community'

origins = [
    "*",
]

@app.websocket("/api/asterisk/ws")
async def websocket_endpoint(websocket: WebSocket):
    queue_wazo = asyncio.Queue()
    queue_fake = asyncio.Queue()

    await websocket.accept(subprotocol='sip')
    asyncio.create_task(client_ws_sip(queue_wazo, queue_fake))
    await queue_wazo.join()
    await queue_fake.join()

    group1 = asyncio.gather(get_websocket_fake(websocket, queue_fake))
    group2 = asyncio.gather(send_websocket_fake(websocket, queue_wazo))
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

async def get_websocket_fake(websocket, queue):
    while True:
        print('Worker to received data from fake websocket')
        data = await websocket.receive_text()
        print('Data received from websocket fake:', data)
        queue.put_nowait(data)

async def send_websocket_fake(websocket, queue):
    while True:
        print('Worker to send data to fake websocket')
        data = await queue.get()
        print('Data received from websocket wazo:', data)
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
    r = requests.get('https://{}/{}'.format(server, full_path), params=params, headers=request.headers)
    try:
        print(r.json())
        return r.json()
    except:
        pass

    return r.content

@app.post("{full_path:path}")
def post_all(full_path: str, item: dict, request: Request):
    print(item)
    r = requests.post('https://{}/{}'.format(server, full_path), json=item, headers=request.headers)
    try:
        print(r.json())
        return r.json()
    except:
        pass

    return r.content

@app.put("{full_path:path}")
def put_all(full_path: str, item: dict, request: Request):
    print(item)
    r = requests.put('https://{}/{}'.format(server, full_path), json=item, headers=request.headers)
    try:
        print(r.json())
        return r.json()
    except:
        pass

    return r.content

@app.delete("{full_path:path}")
def delete_all(full_path: str, request: Request):
    r = requests.delete('https://{}/{}'.format(server, full_path), headers=request.headers)
    return r.text

@app.options("/{full_path:path}")
def options_all(full_path: str):
    r = requests.options('{}/{}'.format(server, full_path))
    return r.text

async def client_ws_sip(queue_wazo, queue_fake):
    uri = "wss://{}/api/asterisk/ws".format(server)
    async with websockets.connect(uri, subprotocols=["sip"]) as ws:
        group1 = asyncio.gather(get_websocket_wazo(ws, queue_wazo))
        group2 = asyncio.gather(send_websocket_wazo(ws, queue_fake))
        all_groups = await asyncio.gather(group1, group2)

async def client_ws_wazo(token, queue_wazo, queue_fake):
    uri = "wss://{}/api/websocketd/?version=2&token={}".format(server, token)
    async with websockets.connect(uri) as ws:
        group1 = asyncio.gather(get_websocket_wazo(ws, queue_wazo))
        group2 = asyncio.gather(send_websocket_wazo(ws, queue_fake))
        all_groups = await asyncio.gather(group1, group2)

async def get_websocket_wazo(websocket, queue):
    while True:
        print('Get data from wazo websocket...')
        data = await websocket.recv()
        print('Received from wazo', data)
        queue.put_nowait(data)

async def send_websocket_wazo(websocket, queue):
    while True:
        data = await queue.get()
        print('Received from wazo queue', data)
        await websocket.send(data)
        queue.task_done()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
