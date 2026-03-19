class RoomFails(Exception): reason = None
class RoomNotExists(RoomFails): reason = "none"
class YouCannotJoin(RoomFails): reason = "play"
class YouCannotPlay(RoomFails): reason = "void"