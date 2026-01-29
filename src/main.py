from secrets import choice
from asyncio import Lock, gather
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from contextlib import asynccontextmanager

class RoomState():
    LOBBY = "lobby"
    PLAYING = "playing"

class RoomRules():
    async def can_join(self, user, room, /):
        if room is None: raise RoomUnexistent()
        if room.host is user: raise HostCannotJoin()
        elif room.state == RoomState.PLAYING: raise JoinNotAllowed()
        else: return True

    async def can_play(self, room, /):
        if len(room.users) == 1: raise PlayNotAllowed()
        else: return True

class RoomFails(Exception):
    reason = "fail"

class RoomUnexistent(RoomFails):
    reason = "none"

class HostCannotJoin(RoomFails):
    reason = "host"

class JoinNotAllowed(RoomFails):
    reason = "play"

class PlayNotAllowed(RoomFails):
    reason = "only"

class Room:
    def __init__(self, user, /):
        while app.state.rooms.setdefault(code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5)), self) is not self: pass
        self.code = code
        self.host = user
        self.users = set()
        self.lock = Lock()
        self.rules = RoomRules()
        self.state = RoomState.LOBBY

    async def __aenter__(self):
        await self.join(self.host)
        await self.host.websocket.send_json({"hook": "code", "data": self.code})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        app.state.rooms.pop(self.code, None)

    async def join(self, user, /):
        async with self.lock: self.users.add(user)
        user.room = self

    async def exit(self, user, /):
        async with self.lock: self.users.discard(user)
        user.room = None

    async def play(self):
        self.state = RoomState.PLAYING
        await self.cast({"hook": "play"})

    async def cast(self, json, /, *, exclude = None): await gather(*(user.websocket.send_json(json) for user in self.users if user is not exclude), return_exceptions = True)

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
    match hook := json.get("hook"), room := app.state.rooms.get(json.get("data")) or room:
        case "join": await room.join(user) if await room.rules.can_join(user, room) else None
        case "room": await room.play() if await room.rules.can_play(room) else None
        case "solo": await room.play()
        case _: await room.cast(json, exclude = user if hook in {"drag", "drop"} else None)

@asynccontextmanager
async def lifespan(app):
    app.state.rooms = {}
    yield
    app.state.rooms.clear()

app = FastAPI(lifespan = lifespan, openapi_url = None)

@app.websocket("/websocket/")
async def websocket(websocket: WebSocket):
    async with User(websocket) as user, Room(user):
        async for json in websocket.iter_json():
            try: await handle(user, user.room, json)
            except RoomFails as fail: await user.websocket.send_json({"hook": "fail", "data": fail.reason})

@app.head("/")
async def status(): return Response(status_code = 200)