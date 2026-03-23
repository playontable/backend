from typing import (
    Union,
    Literal,
    Optional,
    Annotated
)
from pydantic import (
    Field,
    BaseModel,
    TypeAdapter,
    NonNegativeInt,
    StringConstraints
)

class XYZIndex(BaseModel):
    x: float
    y: float
    zIndex: Optional[int] = None

class PlayData(BaseModel): pass
class ItemData(BaseModel): item: NonNegativeInt
class HostData(BaseModel): mode: Literal["room", "solo"]
class JoinData(BaseModel): code: Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{5}$")]
class DotsData(BaseModel):
    item: NonNegativeInt
    dots: XYZIndex

class HostJSON(BaseModel):
    hook: Literal["host"]
    data: HostData

class JoinJSON(BaseModel):
    hook: Literal["join"]
    data: JoinData

class PlayJSON(BaseModel):
    hook: Literal["play"]
    data: PlayData = PlayData()

class StepJSON(BaseModel):
    hook: Literal["step"]
    data: ItemData

class DragJSON(BaseModel):
    hook: Literal["drag"]
    data: DotsData

class CopyJSON(BaseModel):
    hook: Literal["copy"]
    data: DotsData

class HandJSON(BaseModel):
    hook: Literal["hand"]
    data: ItemData

class FallJSON(BaseModel):
    hook: Literal["fall"]
    data: ItemData

class DrawJSON(BaseModel):
    hook: Literal["draw"]
    data: ItemData

class FlipJSON(BaseModel):
    hook: Literal["flip"]
    data: ItemData

class RollJSON(BaseModel):
    hook: Literal["roll"]
    data: ItemData

class WipeJSON(BaseModel):
    hook: Literal["wipe"]
    data: ItemData

adapter = TypeAdapter(
    Annotated[
        Union[
            HostJSON,
            JoinJSON,
            PlayJSON,
            StepJSON,
            DragJSON,
            CopyJSON,
            HandJSON,
            FallJSON,
            DrawJSON,
            FlipJSON,
            RollJSON,
            WipeJSON
        ],
        Field(discriminator = "hook")
    ]
)