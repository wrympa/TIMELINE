from dataclasses import dataclass
from typing import List

from pydantic import BaseModel


class GameState(BaseModel):
    deck: List[int]
    hands: dict[str, List[int]]
    points: dict[str, int]
    currentTurn: str
    over: bool
    pileSize: int
