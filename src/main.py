from secrets import choice
from asyncio import gather
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    app.state.users = {}
    yield
    app.state.users.clear()

class User:
    def __init__(self, websocket, /):
        while app.state.users.setdefault(code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5)), self) is not self: pass
        self.code = code
        self.room = {self}
        self.websocket = websocket

    async def __aenter__(self):
        await self.websocket.accept()
        await self.websocket.send_json({"hook": "code", "data": self.code})
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.room.discard(self)
        if app.state.users.get(self.code) is self: app.state.users.pop(self.code, None)
        await self.websocket.close()

    async def broadcast(self, json, /, *, exclude = None): await self.websocket.send_json({"hook": "fail"}) if json.get("hook") == "room" and len(self.room) <= 1 else await gather(*(user.websocket.send_json(json) for user in self.room if user is not exclude), return_exceptions = True)

async def handle(user, json = None, /):
    if (hook := json.get("hook")) != "join": await user.broadcast(json, exclude = user if hook in {"drag", "hand", "fall"} else None)
    elif (host := app.state.users.get(json.get("data"))) is not None and host is not user:
        for user in (merged := user.room | host.room): user.room = merged

@(app := FastAPI(lifespan = lifespan, openapi_url = None)).websocket("/websocket/")
async def websocket(websocket: WebSocket):
    async with User(websocket) as user:
        async for json in websocket.iter_json(): await handle(user, json)