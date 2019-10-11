import websockets
import requests

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
    await websocket.accept(subprotocol='sip')
    while True:
        data = await websocket.receive_text()
        print(data)
        frames = await client(data)
        await websocket.send_text(frames)

@app.get("{full_path:path}")
def read_all(full_path: str, request: Request):
    r = requests.get('https://{}/{}'.format(server, full_path), headers=request.headers)
    try:
        print(r.json())
        return r.json()
    except:
        pass

    return r.content

@app.options("/{full_path:path}")
def options_all(full_path: str):
    r = requests.options('{}/{}'.format(server, full_path))
    return r.text

async def client(data):
    uri = "wss://{}/api/asterisk/ws".format(server)
    print(uri)
    async with websockets.connect(uri, subprotocols=["sip"]) as ws:
        await ws.send(data)
        frame = await ws.recv()
        print(frame)
        return frame

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
