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

class HostJSON(BaseModel):
    hook: Literal["host"]
    mode: Literal["room", "solo"]

class JoinJSON(BaseModel):
    hook: Literal["join"]
    code: Annotated[str, StringConstraints(pattern = r"^[A-Z0-9]{5}$")]

class PlayJSON(BaseModel):
    hook: Literal["play"]

class StepJSON(BaseModel):
    hook: Literal["step"]
    index: NonNegativeInt

class DragJSON(BaseModel):
    hook: Literal["drag"]
    data: XYZIndex
    index: NonNegativeInt

class CopyJSON(BaseModel):
    hook: Literal["copy"]
    data: XYZIndex
    index: NonNegativeInt

class HandJSON(BaseModel):
    hook: Literal["hand"]
    index: NonNegativeInt

class FallJSON(BaseModel):
    hook: Literal["fall"]
    index: NonNegativeInt

class DrawJSON(BaseModel):
    hook: Literal["draw"]
    index: NonNegativeInt

class FlipJSON(BaseModel):
    hook: Literal["flip"]
    index: NonNegativeInt

class RollJSON(BaseModel):
    hook: Literal["roll"]
    index: NonNegativeInt

class WipeJSON(BaseModel):
    hook: Literal["wipe"]
    index: NonNegativeInt

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