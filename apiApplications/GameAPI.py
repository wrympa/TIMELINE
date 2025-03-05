import json
from asyncio import sleep
import uvicorn
import requests
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from service.GameService import GameService

class GameAPI:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.trueAddress = f"http://{host}:{port}"
        self.addressAddr = "http://127.0.0.1:9090"
        self.gameManagerAddrs = ""
        self.gameService = None
        self.connections = {}

        self.register_routes()

    def register_routes(self):
        # Get game manager address
        auth_response = requests.get(f"{self.addressAddr}/gameManagerAddress")
        self.gameManagerAddrs = f"{auth_response.json()['message']}"
        requests.post(f"{self.gameManagerAddrs}/addServer", json={"address": self.trueAddress})
        print("REGISTERED self as ", self.trueAddress)

        @self.app.post("/resetServer")
        async def reset_server():
            if self.gameService:
                self.gameService.resetService()
            self.connections.clear()
            self.gameService = None  # Reset game state
            return {"message": "STARTED"}

        @self.app.websocket("/ws/{player_id}")
        async def websocket_endpoint(websocket: WebSocket, player_id: str):
            await websocket.accept()
            self.connections[player_id] = websocket
            print(f"Player {player_id} connected.")

            if len(self.connections.keys()) == 4 and self.gameService is None:
                print("All players connected. Starting game...")
                self.gameService = GameService(list(self.connections.keys()))
                print("SENDING STATE")
                await self.broadcast_game_state()

            try:
                while True:
                    while self.gameService is None:
                        await sleep(1)
                    while self.gameService.getCurrentTurnPlayer() != player_id:
                        await sleep(1)

                    print(f"WebSocket endpoint state: {websocket.client_state}")
                    data = await websocket.receive()
                    data = json.loads(data["text"])
                    print(f"DATA IS {data}")
                    if self.gameService:
                        self.gameService.processMove(player_id, data)
                    self.gameService.advance()
                    print("BROADING")
                    await self.broadcast_game_state()

            except WebSocketDisconnect:
                print(f"Player {player_id} disconnected.")
                del self.connections[player_id]
                if len(self.connections) < 4:
                    print("Not enough players. Waiting for reconnection...")

    async def broadcast_game_state(self):
        """Send the updated game state to all players."""
        if self.gameService:
            state = self.gameService.getGameState()
            stateDict = state.dict()
            print("STATE GOT it's", stateDict)
            for player_id, ws in self.connections.items():
                await ws.send_json(stateDict)
        else:
            print("NO GAME SERVICE ?")


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9094
    api = GameAPI(host, port)
    app = api.app
    uvicorn.run(app, host=host, port=port)
