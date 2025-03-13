from pydantic import BaseModel


class StartServerRequest(BaseModel):
    address: str = ""
