from ..play.room import RoomNotExists

async def handle(user, json, /):
    match hook := json.get("hook"):
        case "host" if data := json.get("data"): await user.host(data.get("mode"))
        case "join" if data := json.get("data"):
            if (new := await user.manager.get(data.get("code"))) is None: raise RoomNotExists()
            if user.room is not None and user.room is not new: await user.room.exit(user)
            await new.join(user)
        case "play" if json.get("data") is not None and user.room is not None and user is user.room.host: await user.room.play()
        case "draw" if (data := json.get("data")) is not None and user.room is not None: await user.room.draw(data)
        case "flip" if json.get("data") is not None and user.room is not None: await user.room.send(json)
        case "roll" if (data := json.get("data")) is not None and user.room is not None: await user.room.roll(data.get("item"))
        case "wipe" if (data := json.get("data")) is not None and user.room is not None: await user.room.wipe(data.get("item"))
        case "step" | "drag" | "copy" | "hand" | "fall" if json.get("data") is not None and user.room is not None: await user.room.send(json, exclude = user if hook in ("drag", "hand", "fall") else None)