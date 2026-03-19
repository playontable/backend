from play.user import User
from utils.handler import handle
from utils.monitor import logger
from utils.schema import adapter
from pydantic import ValidationError
from fastapi.responses import Response
from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
    WebSocket
)
from play.room import (
    RoomManager,
    RoomError
)

DECKS = {
    "ita": (
        "01B", "01C", "01D", "01S",
        "02B", "02C", "02D", "02S",
        "03B", "03C", "03D", "03S",
        "04B", "04C", "04D", "04S",
        "05B", "05C", "05D", "05S",
        "06B", "06C", "06D", "06S",
        "07B", "07C", "07D", "07S",
        "08B", "08C", "08D", "08S",
        "09B", "09C", "09D", "09S",
        "10B", "10C", "10D", "10S"
    ),
    "fra": (
        "01C", "01D", "01H", "01S",
        "02C", "02D", "02H", "02S",
        "03C", "03D", "03H", "03S",
        "04C", "04D", "04H", "04S",
        "05C", "05D", "05H", "05S",
        "06C", "06D", "06H", "06S",
        "07C", "07D", "07H", "07S",
        "08C", "08D", "08H", "08S",
        "09C", "09D", "09H", "09S",
        "10C", "10D", "10H", "10S",
        "JC", "JD", "JH", "JS",
        "QC", "QD", "QH", "QS",
        "KC", "KD", "KH", "KS",
        "XB", "XR"
    )
}

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