import sys
import os
import uvicorn
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'service')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))

from StartServerRequest import StartServerRequest
from GameManagerService import GameManagerService
from RegisterAddrRequest import RegisterAddrRequest
from fastapi import FastAPI, HTTPException


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
        try:
            response = requests.post("https://timeline-production-1416.up.railway.app/setGameManagerAddress", json=self.addressStruct.dict())
            print("RESP FOR SETTING ADDRESS OF GameManager ", response.json())
        except Exception as e:
            print(f"Error registering game manager address: {e}")
            print("Continuing anyway, but address service may not be available")

        @self.app.get("/getServer")
        async def getServer():
            print("GET SERVER REQUEST")

            server = self.gameManagerService.isAnyServerFree()
            print(f"Returning server: {server}")
            return {"message": server}

        @self.app.post("/addServer")
        async def addServer(startServerRequest: StartServerRequest):
            print(f"ADD SERVER REQUEST: {startServerRequest.address}")
            if not startServerRequest.address:
                raise HTTPException(status_code=400, detail="Server address is required")

            self.gameManagerService.addNewServer(startServerRequest.address)
            print("ADDED NEW SERVER ", startServerRequest.address)
            return {"message": "ADDED"}

        @self.app.post("/gameFinished")
        async def gameFinished(startServerRequest: StartServerRequest):
            print(f"GAME FINISHED REQUEST: {startServerRequest.address}")
            if not startServerRequest.address:
                raise HTTPException(status_code=400, detail="Server address is required")

            try:
                # Just update the game manager's state without calling back to the game server
                self.gameManagerService.resetServer(startServerRequest.address)
                print("RESET SERVER AFTER GAME FINISHED ", startServerRequest.address)

                # No longer calling back to the game server - it handles its own reset
                print("SUCCESSFUL")
                return {"message": "RESET"}
            except Exception as e:
                print(f"Error processing game finished for server {startServerRequest.address}: {e}")
                raise HTTPException(status_code=500, detail=f"Failed to process game finished: {str(e)}")


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 9093))
    app = GameManagerAPI(host, port).app
    uvicorn.run(app, host=host, port=port)
