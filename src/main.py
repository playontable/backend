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
        self.play = False
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

    async def broadcast(self, json, /, *, exclude = None): await gather(*(user.websocket.send_json(json) for user in self.room if user is not exclude), return_exceptions = True)

async def handle(user, json = None, /):

    hook = json.get("hook")

    if hook == "join":
        host = app.state.users.get(json.get("data"))
        if host is not None:
            if host.play: await user.websocket.send_json({"hook": "fail", "data": "join"})
            elif host is not user:
                for user in (merged := user.room | host.room): user.room = merged
            else: await user.websocket.send_json({"hook": "fail", "data": "same"})
        else: await user.websocket.send_json({"hook": "fail", "data": "room"})
    elif hook == "room":
        if len(user.room) <= 1: await user.websocket.send_json({"hook": "fail", "data": "only"})
        else:
            for user in user.room: user.play = True
            await user.broadcast(json)
    else: await user.broadcast(json, exclude = user if hook in {"drag", "drop"} else None)

app = FastAPI(lifespan = lifespan, openapi_url = None)

@app.websocket("/websocket/")
async def websocket(websocket: WebSocket):
    async with User(websocket) as user:
        async for json in websocket.iter_json(): await handle(user, json)

@app.head("/")
async def status(): return {"status": "ok"}