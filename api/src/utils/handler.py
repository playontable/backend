from random import shuffle
from ..play.room import RoomNotExists

async def handle(user, json, /):
    match hook := json.get("hook"):
        case "host": await user.host(json.get("mode"))
        case "join":
            if (new := await user.manager.get(json.get("code"))) is None: raise RoomNotExists()
            if user.room is not None and user.room is not new: await user.room.exit(user)
            await new.join(user)
        case "play" if user.room is not None and user is user.room.host: await user.room.play()
        case "draw": pass
        case "flip": pass
        case "roll": await user.room.send({"hook": "roll", "data": {"dice": shuffle([1, 2, 3, 4, 5, 6])}})
        case "step" | "drag" | "copy" | "hand" | "fall" | "wipe" if user.room is not None: await user.room.send(json, exclude = user if hook in ("drag", "hand", "fall") else None)