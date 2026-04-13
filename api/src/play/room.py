from secrets import choice
from asyncio import (
    Lock,
    gather
)
from dataclasses import (
    field,
    dataclass
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

@dataclass
class RoomState:
    start: bool = False
    drawn: dict[int, set[str]] = field(default_factory = dict)

    def wipe(self, item, /):
        self.drawn = {index if index < item else index - 1: cards for index, cards in self.drawn.items() if index != item}

class RoomRules:
    def __init__(self, room, /): self.room = room

    def can_join(self):
        if not self.room.state.start: return True
        else: raise YouCannotJoin()

    def can_play(self):
        if len(self.room.users) > 1 and not self.room.state.start: return True
        else: raise YouCannotPlay()

class RoomError(Exception): reason = None
class RoomNotExists(RoomError): reason = "none"
class YouCannotJoin(RoomError): reason = "play"
class YouCannotPlay(RoomError): reason = "void"

class RoomManager:
    def __init__(self):
        self.rooms = {}
        self.lock = Lock()

    async def set(self, user, /):
        async with self.lock:
            while (code := "".join(choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(5))) in self.rooms: pass
            room = Room(code, user, self)
            self.rooms[code] = room
            return room

    async def get(self, code, /):
        async with self.lock: return self.rooms.get(code)

    async def pop(self, code, /):
        async with self.lock: self.rooms.pop(code, None)

    async def end(self):
        async with self.lock: self.rooms.clear()

class Room:
    def __init__(self, code, host, manager, /):
        self.code = code
        self.host = host
        self.lock = Lock()
        self.users = {host}
        self.manager = manager
        self.state = RoomState()
        self.rules = RoomRules(self)

    async def join(self, user, /):
        async with self.lock:
            self.rules.can_join()
            self.users.add(user)
            user.room = self
        await user.websocket.send_json({"hook": "join"})

    async def play(self):
        async with self.lock:
            self.rules.can_play()
            self.state.start = True
        await self.send({"hook": "play"})

    async def exit(self, user, /):
        host = None
        async with self.lock:
            if user.room is not self: return
            self.users.discard(user)
            user.room = None
            if self.users:
                if self.host is user:
                    self.host = next(iter(self.users))
                    if not self.state.start: host = self.host
            else: host = False
        if host is False: await self.manager.pop(self.code)
        elif host is not None: await host.websocket.send_json({"hook": "room", "data": {"code": self.code}})

    async def draw(self, data, /):
        async with self.lock:
            drawn = self.state.drawn.setdefault(data.get("item"), set())
            deck = DECKS[data.get("deck")]
            if data.get("deck") == "fra" and not data.get("jolly"): deck = deck[:-2]
            available = [card for card in deck if card not in drawn]
            if not available:
                drawn.clear()
                available = list(deck)
            card = choice(available)
            drawn.add(card)
        await self.send({"hook": "draw", "data": {"item": data.get("item"), "deck": data.get("deck"), "color": data.get("color"), "card": card}})

    async def roll(self, item, /):
        await self.send({"hook": "roll", "data": {"item": item, "dice": [choice((1, 2, 3, 4, 5, 6)) for _ in range(8)]}})

    async def wipe(self, item, /):
        async with self.lock: self.state.wipe(item)
        await self.send({"hook": "wipe", "data": {"item": item}})

    async def send(self, json, /, *, exclude = None):
        async with self.lock: recipients = [user for user in self.users if user is not exclude]
        await gather(*(user.websocket.send_json(json) for user in recipients), return_exceptions = True)