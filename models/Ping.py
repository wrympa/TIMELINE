from typing import List

from pydantic import BaseModel


class Ping(BaseModel):
    sendJi: str
