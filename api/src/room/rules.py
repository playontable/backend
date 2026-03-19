from .fails import (
    YouCannotJoin,
    YouCannotPlay
)

class RoomRules:
    def __init__(self, room, /): self.room = room

    def can_join(self):
        if not self.room.state.start: return True
        else: raise YouCannotJoin()

    def can_play(self):
        if len(self.room.users) > 1 and not self.room.state.start: return True
        else: raise YouCannotPlay()