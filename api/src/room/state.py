from dataclasses import (
    field,
    dataclass
)

@dataclass
class RoomState:
    start: bool = False
    drawn: dict[int, set[str]] = field(default_factory = dict)