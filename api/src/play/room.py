from secrets import choice
from asyncio import (
    Lock,
    gather
)
from dataclasses import (
    field,
    dataclass
)

@dataclass
class RoomState:
    start: bool = False
    drawn: dict[int, set[str]] = field(default_factory = dict)

class RoomRules:
    def __init__(self, room, /): self.room = room

    def can_join(self):
        if not self.room.state.start: return True
        else: raise YouCannotJoin()

    def can_play(self):
        if len(self.room.users) > 1 and not self.room.state.start: return True
        else: raise YouCannotPlay()

class RoomError(Exception): reason = None
class RoomNotExists(RoomError): reason = "none"
class YouCannotJoin(RoomError): reason = "play"
class YouCannotPlay(RoomError): reason = "void"

class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.lock = Lock()

    async def set(self, user, /):
        async with self.lock:
            while (code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5))) in self.rooms: pass
            room = Room(code, user, self)
            self.rooms[code] = room
            return room

    async def get(self, code, /):
        async with self.lock: return self.rooms.get(code)

    async def pop(self, code, /):
        async with self.lock: self.rooms.pop(code, None)

    async def end(self):
        async with self.lock: self.rooms.clear()

class Room:
    def __init__(self, code, host, manager, /):
        self.code = code
        self.host = host
        self.lock = Lock()
        self.users = {host}
        self.manager = manager
        self.state = RoomState()
        self.rules = RoomRules(self)

    async def join(self, user, /):
        async with self.lock:
            self.rules.can_join()
            self.users.add(user)
            user.room = self

    async def play(self):
        async with self.lock:
            self.rules.can_play()
            self.state.start = True
        await self.send({"hook": "play"})

    async def exit(self, user, /):
        async with self.lock:
            if user.room is not self: return
            self.users.discard(user)
            user.room = None
            if self.users: return
        await self.manager.pop(self.code)

    async def send(self, json, /, *, exclude = None):
        async with self.lock: recipients = [user for user in self.users if user is not exclude]
        await gather(*(user.websocket.send_json(json) for user in recipients), return_exceptions = True)