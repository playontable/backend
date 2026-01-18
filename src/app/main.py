from .user import User
from fastapi import FastAPI, WebSocket
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app):
    app.state.users = {}
    yield

async def handle(users, user, json = None, /):
    if (hook := json.get("hook")) != "join": await user.broadcast(json, exclude = user if hook in {"drag", "hand", "fall"} else None)
    elif (host := users.get(json.get("data"))) is not None and host is not user:
        for user in (merged := user.room | host.room): user.room = merged

app = FastAPI(lifespan = lifespan, openapi_url = None)

@app.websocket("/websocket/")
async def websocket(websocket: WebSocket):
    async with User(websocket, app.state.users) as user:
        async for json in websocket.iter_json(): await handle(app.state.users, user, json)

@app.get("/")
async def status(): return {"status": "okay"}