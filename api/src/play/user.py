class User:
    def __init__(self, manager, websocket, /):
        self.room = None
        self.manager = manager
        self.websocket = websocket

    async def __aenter__(self):
        await self.websocket.accept()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.room is not None: await self.room.exit(self)
        await self.websocket.close()

    async def host(self, mode, /):
        if mode in ("room", "solo"):
            self.room = self.room or await self.manager.set(self)
            await self.websocket.send_json({"hook": "room", "data": {"code": self.room.code}} if mode == "room" else {"hook": "play", "data": {}})