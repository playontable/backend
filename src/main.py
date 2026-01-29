from enum import Enum
from secrets import choice
from asyncio import Lock, gather
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager

class RoomState(str, Enum):
    LOBBY = "lobby"
    PLAYING = "playing"

class RoomRules():
    def __init__(self, room, /): self.room = room

    async def can_join(self, user, /):
        if self.room.host is user: return False, "host"
        elif self.room.state is RoomState.PLAYING: return False, "play"
        else: return True, None

    async def can_play(self):
        if len(self.room.users) == 1: return False, "only"
        else: return True, None

class Room:
    def __init__(self, user, /):
        while app.state.rooms.setdefault(code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5)), self) is not self: pass
        self.code = code
        self.host = user
        self.users = set()
        self.lock = Lock()
        self.rules = RoomRules(self)
        self.state = RoomState.LOBBY

    async def __aenter__(self):
        await self.join(self.host)
        await self.host.websocket.send_json({"hook": "code", "data": self.code})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        app.state.rooms.pop(self.code, None)

    async def join(self, user, /):
        user.room = self
        async with self.lock: self.users.add(user)

    async def exit(self, user, /):
        async with self.lock: self.users.discard(user)

    async def play(self):
        self.state = RoomState.PLAYING
        await self.cast({"hook": "play"})

    async def cast(self, json, /, *, exclude = None):
        async with self.lock: await gather(*(user.websocket.send_json(json) for user in self.users if user is not exclude), return_exceptions = True)

class User:
    def __init__(self, websocket, /):
        self.room = None
        self.websocket = websocket

    async def __aenter__(self):
        await self.websocket.accept()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.room is not None: await self.room.exit(self)
        await self.websocket.close()

async def handle(user, room, json = None, /):
    match hook := json.get("hook"):
        case "join":
            room = app.state.rooms.get(json.get("data"))
            permit, reason = await room.rules.can_join(user)
            if permit: await room.join(user)
            else: await user.websocket.send_json({"hook": "fail", "data": reason})
        case "room":
            permit, reason = await user.room.rules.can_play()
            if permit: await user.room.play()
            else: await user.websocket.send_json({"hook": "fail", "data": reason})
        case "solo": await room.play()
        case _: await user.room.cast(json, exclude = user if hook in {"drag", "drop"} else None)

@asynccontextmanager
async def lifespan(app):
    app.state.rooms = {}
    yield
    app.state.rooms.clear()

app = FastAPI(lifespan = lifespan, openapi_url = None)

@app.websocket("/websocket/")
async def websocket(websocket: WebSocket):
    async with User(websocket) as user, Room(user) as room:
        async for json in websocket.iter_json(): await handle(user, room, json)

@app.head("/")
async def status(): return {"status": "ok"}

if __name__ == "__main__": import uvicorn; uvicorn.run("main:app", reload = True)