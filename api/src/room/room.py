from .state import RoomState
from .rules import RoomRules
from asyncio import (
    Lock,
    gather
)

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