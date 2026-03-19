from .room import Room
from asyncio import Lock
from secrets import choice

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