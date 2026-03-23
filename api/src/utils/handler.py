from random import shuffle
from ..play.room import RoomNotExists

async def handle(user, json, /):
    match hook := json.get("hook"):
        case "host" if data := json.get("data"): await user.host(data.get("mode"))
        case "join" if data := json.get("data"):
            if (new := await user.manager.get(data.get("code"))) is None: raise RoomNotExists()
            if user.room is not None and user.room is not new: await user.room.exit(user)
            await new.join(user)
        case "play" if data := json.get("data") and user.room is not None and user is user.room.host: await user.room.play()
        case "draw" if data := json.get("data") and user.room is not None: pass
        case "flip" if data := json.get("data") and user.room is not None: pass
        case "roll" if data := json.get("data") and user.room is not None: await user.room.send({"hook": "roll", "data": {"dice": shuffle([1, 2, 3, 4, 5, 6])}})
        case "step" | "drag" | "copy" | "hand" | "fall" | "wipe" if data := json.get("data") and user.room is not None: await user.room.send(json, exclude = user if hook in ("drag", "hand", "fall") else None)