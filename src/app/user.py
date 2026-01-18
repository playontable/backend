from secrets import choice
from asyncio import gather

class User:
    def __init__(self, websocket, users, /):
        while users.setdefault(code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5)), self) is not self: pass
        self.code = code
        self.room = {self}
        self._users = users
        self.websocket = websocket

    async def __aenter__(self):
        await self.websocket.accept()
        await self.websocket.send_json({"hook": "code", "data": self.code})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.room.discard(self)
        if self._users.get(self.code) is self: self._users.pop(self.code, None)
        await self.websocket.close()

    async def broadcast(self, json, /, *, exclude = None): await self.websocket.send_json({"hook": "fail"}) if json.get("hook") == "room" and len(self.room) <= 1 else await gather(*(user.websocket.send_json(json) for user in self.room if user is not exclude), return_exceptions = True)