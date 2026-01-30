from enum import StrEnum
from secrets import choice
from asyncio import Lock, gather
from fastapi import FastAPI, WebSocket
from fastapi.responses import Response
from contextlib import asynccontextmanager
from typing import Union, Literal, Annotated
from pydantic import Field, BaseModel, TypeAdapter, NonNegativeInt, ValidationError, StringConstraints

class RoomState(StrEnum):
    LOBBY = "LOBBY"
    START = "START"

class RoomRules():
    def __init__(self, room, /): self.room = room

    def can_join(self, /):
        if self.room.state == RoomState.START: raise JoinWhileLobby()
        else: return True

    def can_play(self, user, /):
        if len(self.room.users) <= 1: raise RoomMustBeFull()
        elif user is not self.room.host: raise OnlyHostStarts()
        else: return True

class RoomFails(Exception): reason = None
class RoomHasToExist(RoomFails): reason = "none"
class JoinWhileLobby(RoomFails): reason = "play"
class RoomMustBeFull(RoomFails): reason = "void"
class OnlyHostStarts(RoomFails): reason = ""

class Room:
    def __init__(self, user, /):
        while app.state.rooms.setdefault(code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5)), self) is not self: pass
        self.code = code
        self.host = user
        self.users = set()
        self.lock = Lock()
        self.rules = RoomRules(self)
        self.state = RoomState("LOBBY")

    async def __aenter__(self):
        await self.join(self.host)
        await self.host.websocket.send_json({"hook": "code", "data": self.code})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.users.clear()
        app.state.rooms.pop(self.code, None)

    async def join(self, user, /):
        async with self.lock:
            if self.rules.can_join():
                self.users.add(user)
                user.room = self

    async def exit(self, user, /):
        async with self.lock:
            if user.room is not self: return
            self.users.discard(user)
            user.room = None
            empty = (len(self.users) == 0)
        if empty: app.state.rooms.pop(self.code, None)

    async def play(self, user, /):
        async with self.lock:
            if self.rules.can_play(user): self.state = RoomState("START")
        await self.cast({"hook": "play"})

    async def cast(self, json, /, *, exclude = None):
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

async def handle(user, json = None, /):
    match hook := json.get("hook"):
        case "join":
            new = app.state.rooms.get(json["data"])
            if new is None: raise RoomHasToExist()

            old = user.room
            if old is not None and old is not new: await old.exit(user)

            await new.join(user)
        case "room": await user.room.play(user)
        case _: await user.room.cast(json, exclude = user if hook in {"drag", "drop"} else None)

class DragData(BaseModel):
    x: int
    y: int

class CopyData(BaseModel):
    x: int
    y: int

class RoomJSON(BaseModel):
    hook: Literal["room"]

class JoinJSON(BaseModel):
    hook: Literal["join"]
    data: Annotated[str, StringConstraints(pattern = r"^[A-Z0-9]{5}$")]

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
    data: DragData
    index: NonNegativeInt

class CopyJSON(BaseModel):
    hook: Literal["copy"]
    data: CopyData
    index: NonNegativeInt

adapter = TypeAdapter(Annotated[Union[RoomJSON, JoinJSON, DropJSON, RollJSON, WipeJSON, StepJSON, DragJSON, CopyJSON], Field(discriminator = "hook")])

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
            try: await handle(user, adapter.validate_python(json).model_dump())
            except ValidationError: pass
            except RoomFails as fail: await user.websocket.send_json({"hook": "fail", "data": fail.reason})

@app.head("/")
async def status(): return Response()