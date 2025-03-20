import asyncio
import json
import os
import sys
from asyncio import sleep, create_task, CancelledError
from datetime import datetime

import uvicorn
import requests
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'service')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))

from Ping import Ping
from GameService import GameService


class GameAPI:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.trueAddress = f"https://timeline-production-1ea7.up.railway.app"
        self.addressAddr = "https://timeline-production-1416.up.railway.app"
        self.gameManagerAddrs = ""
        self.gameService = None
        self.connections = {}
        self.game_over = False
        self.connection_monitor_task = None

        self.register_routes()

    def register_routes(self):
        # Get game manager address
        auth_response = requests.get(f"{self.addressAddr}/gameManagerAddress")
        self.gameManagerAddrs = f"{auth_response.json()['message']}"
        requests.post(f"{self.gameManagerAddrs}/addServer", json={"address": self.trueAddress})
        print("REGISTERED self as ", self.trueAddress)

        @self.app.get("/")
        async def root():
            return {"message": "Server is running!"}

        @self.app.post("/resetServer")
        async def reset_server():
            print("Reset server called - cleaning up resources")
            await self.reset_server_internal()
            return {"message": "RESET"}

        @self.app.get("/gameStatus")
        async def game_status():
            return {
                "active": self.gameService is not None,
                "players_connected": len(self.connections),
                "game_over": self.game_over
            }

        @self.app.websocket("/ws/{player_id}")
        async def websocket_endpoint(websocket: WebSocket, player_id: str):
            await websocket.accept()

            # Store the connection
            self.connections[player_id] = websocket
            print(f"Player {player_id} connected.")

            # If all players are connected and game not started, start game
            print("playazz", len(self.connections.keys()))
            if len(self.connections.keys()) == 4 and self.gameService is None:
                print("All players connected. Starting game...")
                self.gameService = GameService(list(self.connections.keys()))
                self.game_over = False  # Reset game_over flag on new game start
                print("SENDING STATE")
                await self.broadcast_game_state()

                # Start monitoring connections after game starts
                if not self.connection_monitor_task or self.connection_monitor_task.done():
                    self.connection_monitor_task = create_task(self.monitor_connections())

            try:
                while self.gameService is None:
                    await sleep(1)

                # Wait until it's this player's turn
                while not self.game_over:
                    print(f"WebSocket endpoint state: {websocket.client_state}")
                    # data = await websocket.receive()

                    data = await asyncio.wait_for(
                        websocket.receive_text(),
                        timeout=300.0  # 60 seconds timeout
                    )
                    # Check if game is still active before processing move

                    data = json.loads(data)
                    print("DATA IS", data)

                    try:
                        pingInfo = data["sendJi"]
                        print(f"PING INFO FROM {player_id}", pingInfo)
                    except KeyError:
                        if self.gameService:
                            self.gameService.processMove(player_id, data)
                            self.gameService.advance()
                            print("BROADCASTING")
                            await self.broadcast_game_state()

            except WebSocketDisconnect:
                print(f"Player {player_id} disconnected.")
                if player_id in self.connections:
                    del self.connections[player_id]

                if len(self.connections) < 4 and not self.game_over and self.gameService:
                    print("Not enough players. Waiting for reconnection...")
                else:
                    print("Game cannot continue - not enough players")
                    self.game_over = True
                    await self.finish_game()
            except CancelledError:
                print(f"Websocket task for {player_id} was cancelled")
            except Exception as e:
                print(f"Error in websocket handler for {player_id}: {e}")
                if player_id in self.connections:
                    del self.connections[player_id]

                if len(self.connections) < 4 and self.gameService:
                    print("Error caused player disconnect. Waiting for reconnection...")

    async def reset_server_internal(self):
        """Internal method to reset server state"""
        # Close all websocket connections
        for player_id, ws in list(self.connections.items()):
            try:
                await ws.close(code=1000)
            except Exception as e:
                print(f"Error closing websocket for {player_id}: {e}")

        # Clear connections and reset state
        self.connections.clear()
        self.gameService = None

        # Cancel and clean up any ongoing tasks
        if self.connection_monitor_task:
            try:
                self.connection_monitor_task.cancel()
                await sleep(0.1)
            except Exception as e:
                print(f"Error cancelling task: {e}")
            self.connection_monitor_task = None

        self.game_over = False
        print("Server reset complete")

    async def finish_game(self):
        """Clean up game resources and notify game manager."""
        print("FINISHING GAME")

        # Reset server first (handle all cleanup)
        await self.reset_server_internal()

        # Then notify game manager asynchronously (don't wait for response)
        create_task(self.notify_game_manager())

    async def notify_game_manager(self):
        """Asynchronously notify the game manager that the game is finished."""
        try:
            # Use httpx for async HTTP with timeout
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.gameManagerAddrs}/gameFinished",
                    json={"address": self.trueAddress},
                    timeout=5.0  # Add timeout to prevent hanging
                )
            print(f"Notified game manager that game at {self.trueAddress} is finished")
        except Exception as e:
            print(f"Failed to notify game manager of game end: {e}")

    async def monitor_connections(self):
        try:
            while not self.game_over:
                await sleep(5)

                pingInfo = Ping(sendJi=str(datetime.utcnow().timestamp()))
                pingInfo = pingInfo.dict()

                for player_id, ws in self.connections.items():
                    print("SENDING STATE TO", player_id)
                    await ws.send_json(pingInfo)

                if self.gameService and len(self.connections) < 4:
                    print("Game over via DC")
                    self.game_over = True

                    state = self.gameService.getGameState()
                    stateDict = state.dict()
                    stateDict["over"] = True
                    for player_id, ws in self.connections.items():
                        print("SENDING STATE TO", player_id)
                        await ws.send_json(stateDict)
                    break

            await self.finish_game()
            print("Connection monitor task ending")
        except CancelledError:
            print("Connection monitor task was cancelled")
        except Exception as e:
            print(f"Connection monitor error: {e}")

    async def broadcast_game_state(self):
        """Send the updated game state to all players."""
        if self.gameService:
            try:
                state = self.gameService.getGameState()
                stateDict = state.dict()
                print("STATE GOT it's", stateDict)

                if stateDict.get("over", False):
                    self.game_over = True

                for player_id, ws in self.connections.items():
                    print("SENDING STATE TO", player_id)
                    await ws.send_json(stateDict)

                if self.game_over:
                    print("Game over detected during broadcast")
                    await self.finish_game()
            except Exception as e:
                print(f"Error during broadcast: {e}")
        else:
            print("NO GAME SERVICE ?")


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 9094))
    app = GameAPI(host, port).app
    uvicorn.run(app, host=host, port=port)
