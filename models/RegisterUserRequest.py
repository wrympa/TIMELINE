from pydantic import BaseModel


class RegisterUserRequest(BaseModel):
    userName: str = ""
    password: str = ""
