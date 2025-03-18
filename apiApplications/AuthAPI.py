import sys
import os

import uvicorn
import requests

from fastapi import FastAPI

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'service')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))
from RegisterAddrRequest import RegisterAddrRequest
from RegisterUserRequest import RegisterUserRequest
from AccountDAO import AccountDAO


class AuthAPI:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.authDAO = AccountDAO()
        self.addressStruct = RegisterAddrRequest()
        self.addressStruct.address = f"https://timeline-production-79fd.up.railway.app"

        self.register_routes()

    def register_routes(self):
        response = requests.post("https://timeline-production-1416.up.railway.app/setAuthAddress", json=self.addressStruct.model_dump())
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
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 9091))
    app = AuthAPI(host, str(port)).app
    uvicorn.run(app, host=host, port=port)
