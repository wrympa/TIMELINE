import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
import requests

from fastapi import FastAPI

from models.RegisterAddrRequest import RegisterAddrRequest
from models.RegisterUserRequest import RegisterUserRequest
from service.AccountDAO import AccountDAO


class AuthAPI:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.authDAO = AccountDAO()
        self.addressStruct = RegisterAddrRequest()
        self.addressStruct.address = f"http://{host}:{port}"

        self.register_routes()

    def register_routes(self):
        response = requests.post("http://127.0.0.1:9090/setAuthAddress", json=self.addressStruct.model_dump())
        print("RESP FOR SETTING ADDRESS OF QUEUE ", response.json())

        @self.app.post("/tryRegister")
        async def attempt_registration(request: RegisterUserRequest):
            result = self.authDAO.addAccount(request.userName, request.password)
            answer = "SUCCESSFULLY REGISTERED" if result else "USER IS LIKELY TAKEN"
            print("ATTEMPT TO REGISTER: ", answer)
            return {"message": answer}

        @self.app.get("/tryAuth")  # Changed to post method
        async def attempt_authentication(request: RegisterUserRequest):  # Changed parameter name and type
            result = self.authDAO.attemptAuth(request.userName, request.password)
            answer = "SUCCESSFULLY LOGGED IN" if result else "WRONG CREDENTIALS"
            print("ATTEMPT TO AUTH: ", answer)
            return {"message": answer}


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9091
    api = AuthAPI(host, port)
    uvicorn.run(api.app, host=host, port=port)
