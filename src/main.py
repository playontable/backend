from enum import Enum
from secrets import choice
from asyncio import Lock, gather
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager

class RoomState(str, Enum):
    LOBBY = "lobby"
    PLAYING = "playing"

class Room:
    def __init__(self):
        self.lock = Lock()
        self.users = set()
        self.state = RoomState.LOBBY

    async def join(self, user, /):
        async with self.lock:
            if self.state is RoomState.PLAYING: return False
            self.users.add(user)
            user.room = self
            return True

    async def play(self):
        async with self.lock:
            if len(self.users) <= 1: return False
            self.state = RoomState.PLAYING
            return True

    async def exit(self, user, /):
        async with self.lock: self.users.discard(user)

    async def broadcast(self, json, /, *, exclude = None): await gather(*(user.websocket.send_json(json) for user in self.users if user is not exclude), return_exceptions = True)

class User:
    def __init__(self, websocket, /):
        while app.state.users.setdefault(code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5)), self) is not self: pass
        self.code = code
        self.room = Room()
        self.websocket = websocket

    async def __aenter__(self):
        await self.room.join(self)
        await self.websocket.accept()
        await self.websocket.send_json({"hook": "code", "data": self.code})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.room.exit(self)
        if app.state.users.get(self.code) is self: app.state.users.pop(self.code, None)
        await self.websocket.close()

async def handle(user, json = None, /):
    match hook := json.get("hook"):
        case "join":
            host = app.state.users.get(json.get("data").upper())
            if host is None: await user.websocket.send_json({"hook": "fail", "data": "room"})
            elif host is user: await user.websocket.send_json({"hook": "fail", "data": "same"})
            elif not await host.room.join(user): await user.websocket.send_json({"hook": "fail", "data": "join"})
        case "room":
            if not await user.room.play(): await user.websocket.send_json({"hook": "fail", "data": "only"})
            else: await user.room.broadcast(json)
        case _: await user.room.broadcast(json, exclude = user if hook in {"drag", "drop"} else None)

@asynccontextmanager
async def lifespan(app):
    app.state.users = {}
    yield
    app.state.users.clear()

app = FastAPI(lifespan = lifespan, openapi_url = None)

@app.websocket("/websocket/")
async def websocket(websocket: WebSocket):
    async with User(websocket) as user:
        async for json in websocket.iter_json(): await handle(user, json)

@app.head("/")
async def status(): return {"status": "ok"}