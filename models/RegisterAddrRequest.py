from pydantic import BaseModel


class RegisterAddrRequest(BaseModel):
    address: str = ""
