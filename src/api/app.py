from secrets import choice
from asyncio import Lock, gather
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from logging import ERROR, getLogger, basicConfig
from typing import Union, Literal, Optional, Annotated
from pydantic import Field, BaseModel, TypeAdapter, NonNegativeInt, ValidationError, StringConstraints

DECKS = {
    "ita": (
        "01B", "01C", "01D", "01S",
        "02B", "02C", "02D", "02S",
        "03B", "03C", "03D", "03S",
        "04B", "04C", "04D", "04S",
        "05B", "05C", "05D", "05S",
        "06B", "06C", "06D", "06S",
        "07B", "07C", "07D", "07S",
        "08B", "08C", "08D", "08S",
        "09B", "09C", "09D", "09S",
        "10B", "10C", "10D", "10S"
    ),
    "fra": (
        "01C", "01D", "01H", "01S",
        "02C", "02D", "02H", "02S",
        "03C", "03D", "03H", "03S",
        "04C", "04D", "04H", "04S",
        "05C", "05D", "05H", "05S",
        "06C", "06D", "06H", "06S",
        "07C", "07D", "07H", "07S",
        "08C", "08D", "08H", "08S",
        "09C", "09D", "09H", "09S",
        "10C", "10D", "10H", "10S",
        "JC", "JD", "JH", "JS",
        "QC", "QD", "QH", "QS",
        "KC", "KD", "KH", "KS",
        "XB", "XR"
    )
}

@dataclass
class RoomState:
    start: bool = False
    drawn: dict[int, set[str]] = field(default_factory = dict)

class RoomRules:
    def __init__(self, room, /): self.room = room

    def can_join(self):
        if self.room.state.start: raise JoinWhileLobby()
        else: return True

    def can_play(self):
        if len(self.room.users) <= 1: raise RoomNotBeEmpty()
        else: return True

class RoomFails(Exception): reason = None
class RoomHasToExist(RoomFails): reason = "none"
class JoinWhileLobby(RoomFails): reason = "play"
class RoomNotBeEmpty(RoomFails): reason = "void"

class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.lock = Lock()

    async def set(self, user, /):
        async with self.lock:
            while (code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5))) in self.rooms: pass
            room = Room(code, user)
            self.rooms[code] = room
            return room

    async def get(self, code, /):
        async with self.lock: return self.rooms.get(code)

    async def pop(self, code, /):
        async with self.lock: self.rooms.pop(code, None)

    async def end(self):
        async with self.lock: self.rooms.clear()

class Room:
    def __init__(self, code, host):
        self.code = code
        self.host = host
        self.lock = Lock()
        self.users = {host}
        self.state = RoomState()
        self.rules = RoomRules(self)

    async def join(self, user, /):
        async with self.lock:
            if self.rules.can_join():
                self.users.add(user)
                user.room = self

    async def play(self, mode, /):
        async with self.lock:
            if self.state.start: return
            if mode == "room": self.rules.can_play()
            self.state.start = True
        await self.send({"hook": "play"})

    async def exit(self, user, /):
        async with self.lock:
            if user.room is not self: return
            self.users.discard(user)
            user.room = None
            if self.users: return
        await app.state.room_manager.pop(self.code)

    async def send(self, json, /, *, exclude = None):
        async with self.lock: recipients = [user for user in self.users if user is not exclude]
        await gather(*(user.websocket.send_json(json) for user in recipients), return_exceptions = True)

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

    async def host(self):
        if self.room is None:
            self.room = await app.state.room_manager.set(self)
            await self.websocket.send_json({"hook": "code", "data": self.room.code})

async def handle(user, json, /):
    match hook := json.get("hook"):
        case "host": await user.host()
        case "join":
            if (new := await app.state.room_manager.get(json.get("data"))) is None: raise RoomHasToExist()
            if user.room is not None and user.room is not new: await user.room.exit(user)
            await new.join(user)
        case "play" if user.room is not None: await user.room.play(json.get("mode"))
        case "drop" | "roll" | "wipe" | "step" | "drag" | "copy" if user.room is not None: await user.room.send(json, exclude = user if hook in ("drag", "hand", "fall") else None)

class XYZIndex(BaseModel):
    x: float
    y: float
    zIndex: Optional[int] = None

class HostJSON(BaseModel):
    hook: Literal["host"]

class JoinJSON(BaseModel):
    hook: Literal["join"]
    data: Annotated[str, StringConstraints(pattern = r"^[A-Z0-9]{5}$")]

class PlayJSON(BaseModel):
    hook: Literal["play"]
    mode: Literal["room", "solo"]

class DropJSON(BaseModel):
    hook: Literal["drop"]
    index: NonNegativeInt

class RollJSON(BaseModel):
    hook: Literal["roll"]
    data: Annotated[list[Annotated[int, Field(ge = 1, le = 6)]], Field(min_length = 6, max_length = 6)]
    index: NonNegativeInt

class WipeJSON(BaseModel):
    hook: Literal["wipe"]
    index: NonNegativeInt

class StepJSON(BaseModel):
    hook: Literal["step"]
    index: NonNegativeInt

class DragJSON(BaseModel):
    hook: Literal["drag"]
    data: XYZIndex
    index: NonNegativeInt

class CopyJSON(BaseModel):
    hook: Literal["copy"]
    data: XYZIndex
    index: NonNegativeInt

adapter = TypeAdapter(
    Annotated[
        Union[
            HostJSON,
            JoinJSON,
            PlayJSON,
            DropJSON,
            RollJSON,
            WipeJSON,
            StepJSON,
            DragJSON,
            CopyJSON
        ],
        Field(discriminator = "hook")
    ]
)

basicConfig(level = ERROR, format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = getLogger("WebSocket")

@asynccontextmanager
async def lifespan(app):
    app.state.room_manager = RoomManager()
    yield
    await app.state.room_manager.end()

app = FastAPI(lifespan = lifespan, openapi_url = None)

@app.websocket("/websocket/")
async def websocket(websocket: WebSocket):
    async with User(websocket) as user:
        async for json in websocket.iter_json():
            try: await handle(user, adapter.validate_python(json).model_dump())
            except RoomFails as fail: await user.websocket.send_json({"hook": "fail", "data": fail.reason})
            except ValidationError as info:
                for error in info.errors(): logger.error("ValidationError\n\nUSER = %s\nJSON = %s\nINFO = %s\n\n", getattr(user, "websocket"), json, error["msg"])

@app.head("/")
async def status(): return Response()