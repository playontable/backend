from .play.user import User
from .utils.handler import handle
from .utils.monitor import logger
from .utils.schema import adapter
from pydantic import ValidationError
from fastapi.responses import Response
from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
    WebSocket
)
from .play.room import (
    RoomManager,
    RoomError
)

@asynccontextmanager
async def lifespan(app):
    app.state.manager = RoomManager()
    yield
    await app.state.manager.end()

app = FastAPI(lifespan = lifespan, openapi_url = None)

@app.websocket("/websocket/")
async def websocket(websocket: WebSocket):
    async with User( websocket.app.state.manager, websocket) as user:
        async for json in websocket.iter_json():
            try: await handle(user, adapter.validate_python(json).model_dump())
            except RoomError as fail: await user.websocket.send_json({"hook": "fail", "data": fail.reason})
            except ValidationError as info:
                for error in info.errors(): logger.error("ValidationError\n\nUSER = %s\nJSON = %s\nINFO = %s\n\n", getattr(user, "websocket"), json, error["msg"])

@app.head("/")
async def status(): return Response()