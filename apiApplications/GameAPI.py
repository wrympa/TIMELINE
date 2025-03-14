import asyncio
import json
from asyncio import sleep, create_task, CancelledError
import uvicorn
import requests
import httpx
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
        self.game_over = False
        self.connection_monitor_task = None

        self.register_routes()

    def register_routes(self):
        # Get game manager address
        auth_response = requests.get(f"{self.addressAddr}/gameManagerAddress")
        self.gameManagerAddrs = f"{auth_response.json()['message']}"
        requests.post(f"{self.gameManagerAddrs}/addServer", json={"address": self.trueAddress})
        print("REGISTERED self as ", self.trueAddress)

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

            # Check if this is a reconnect during an active game
            is_reconnect = self.gameService is not None and player_id in self.gameService.getPlayers()

            # Store the connection
            self.connections[player_id] = websocket
            print(f"Player {player_id} connected. Reconnect: {is_reconnect}")

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

            # If this is a reconnect, send the current state to the player
            elif is_reconnect:
                try:
                    state = self.gameService.getGameState()
                    await websocket.send_json(state.dict())
                except Exception as e:
                    print(f"Error sending state on reconnect to {player_id}: {e}")

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

    async def check_game_over(self):
        """Check if the game is over based on connection count and game state."""
        if self.gameService and (self.game_over or (self.gameService.getGameState().over)):
            print("GAME OVER detected")
            self.game_over = True
            await self.finish_game()

    async def monitor_connections(self):
        """Continuously monitor connections to detect game over state."""
        try:
            while not self.game_over:
                await sleep(5)

                # Check if game is over through the game state
                if self.gameService and self.gameService.getGameState().over:
                    print("Game over detected by monitor")
                    self.game_over = True
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

                # Update game_over status from state
                if stateDict.get("over", False):
                    self.game_over = True

                # Send state to all connected players
                disconnected_players = []
                for player_id, ws in self.connections.items():
                    try:
                        await ws.send_json(stateDict)
                    except Exception as e:
                        print(f"Error sending to {player_id}: {e}")
                        disconnected_players.append(player_id)

                # Remove disconnected players
                for player_id in disconnected_players:
                    if player_id in self.connections:
                        del self.connections[player_id]

                # Check if game should end due to disconnections
                if len(self.connections) < 4 and not self.game_over:
                    print(f"Not enough players ({len(self.connections)}/4) after broadcasting")

                # Check if game is over
                if self.game_over:
                    print("Game over detected during broadcast")
                    await self.finish_game()
            except Exception as e:
                print(f"Error during broadcast: {e}")
        else:
            print("NO GAME SERVICE ?")


if __name__ == "__main__":
    host = "127.0.0.1"
    port = 9094
    api = GameAPI(host, port)
    app = api.app
    uvicorn.run(app, host=host, port=port)