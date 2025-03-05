import sys
import os

from models.StartServerRequest import StartServerRequest
from service.GameManagerService import GameManagerService

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
import requests

from models.EnqueueRequest import EnqueueRequest
from models.RegisterAddrRequest import RegisterAddrRequest
from fastapi import FastAPI



class GameManagerAPI:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.gameManagerService = GameManagerService()
        self.addressStruct = RegisterAddrRequest()
        self.addressStruct.address = f"http://{host}:{port}"
        self.register_routes()

    def register_routes(self):
        response = requests.post("http://127.0.0.1:9090/setGameManagerAddress", json=self.addressStruct.dict())
        print("RESP FOR SETTING ADDRESS OF GameManager ", response.json())

        @self.app.get("/getServer")
        async def getServer():
            print("GET\n")
            return {"message": self.gameManagerService.isAnyServerFree()}

        @self.app.post("/addServer")
        async def addServer(startServerRequest: StartServerRequest):
            print("ADD\n")
            self.gameManagerService.addNewServer(startServerRequest.address)
            print("ADDED NEW SERVER ", startServerRequest.address)
            return {"message": "ADDED"}

        @self.app.post("/resetServer")
        async def PrepareServer(startServerRequest: StartServerRequest):
            print("RESET\n")
            self.gameManagerService.resetServer(startServerRequest.address)
            print("STARTED SERVER ", startServerRequest.address)
            return {"message": "STARTED"}


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9093
    api = GameManagerAPI(host, port)
    app = api.app
    uvicorn.run(app, host=host, port=port)
