from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class EnqueueRequest(BaseModel):
    UUID: str
