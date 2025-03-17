from typing import List

from pydantic import BaseModel


class PlayerMove(BaseModel):
    cardIndex: int
    cardPlaces: List[int]
