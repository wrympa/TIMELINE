import random
import string
import uuid
import asyncio
import websockets
import requests
import json
import atexit
from typing import List
from urllib.parse import urlparse

from models.PlayerMove import PlayerMove


class ClientService:
    def __init__(self):
        self.pileSize: int = 0
        self.gamePoints: dict[str, int] = {}
        self.gameOver: bool = False
        self.hand: List[int] = []
        self.deck: List[int] = []
        self.myTurn = False
        characters = string.ascii_letters
        self.currName = "GUEST" + ''.join(random.choice(characters) for _ in range(10))
        self.loggedOn = False
        self.addressAddr = "http://127.0.0.1:9090"
        self.websocket = None

        # Get service addresses
        self.get_service_addresses()
        atexit.register(self.cleanup)

        # Use asyncio to run the main client loop
        asyncio.run(self.start_client())

    def get_service_addresses(self):
        auth_response = requests.get(f"{self.addressAddr}/authAddress")
        self.authAddrs = f"{auth_response.json()['message']}"
        print(f"Auth address: {self.authAddrs}")

        queue_response = requests.get(f"{self.addressAddr}/queueAddress")
        self.queAddrs = f"{queue_response.json()['message']}"
        print(f"Queue address: {self.queAddrs}")

        self.gameAddrs = None

    async def start_client(self):
        print(f"""
        HI, [{self.currName}] welcome to [INSERT GAME NAME HERE]
        first sign up/log in
        sign up = REG [USRNAME] [PASS]
        log in = LOG [USRNAME] [PASS]
        enter queue = QUE
        quit = QUIT
        """)

        while True:
            currCommand = input("### : ")
            if currCommand == "QUIT":
                break

            parts = currCommand.split(" ")
            if parts[0] == "REG":
                self.attemptRegister(parts)
            elif parts[0] == "LOG":
                self.attemptAuth(parts)
            elif parts[0] == "QUE":
                await self.attemptEnqueue()

        self.cleanup()

    async def attemptEnqueue(self):
        self.currentGameUUID = str(uuid.uuid4())
        enqueue_data = {
            "UUID": self.currentGameUUID,
        }
        result = requests.post(f"{self.queAddrs}/enqueue", json=enqueue_data).json()["message"]
        if result == "ENQUEUED":
            await self.awaitResponse()
        else:
            print("SOMETHING WRONG WITH SERVER OR UR BANNED")

    async def awaitResponse(self):
        while True:
            await asyncio.sleep(5)
            print("USER IS WAITING")
            enqueue_data = {"UUID": self.currentGameUUID}
            result = requests.get(f"{self.queAddrs}/pollForSelf", json=enqueue_data).json()["message"]
            if result != "Waiting":
                self.gameAddrs = result
                break

        print("MATCH FOUND, STARTING GAME")
        await self.connect_to_websocket()

    async def connect_to_websocket(self):
        parsed_url = urlparse(self.gameAddrs)
        uri = f"ws://{parsed_url.hostname}:{parsed_url.port}/ws/{self.currName}"
        print(uri)

        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to game server!")
                self.websocket = websocket

                # Use a single task manager to handle receive and send
                await self.manage_game_tasks(websocket)

        except websockets.exceptions.WebSocketException as e:
            print(f"WebSocket error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
        finally:
            await self.postGameCleanUp()

    async def postGameCleanUp(self):
        if self.websocket:
            await self.websocket.close()
            print("GAME OVER: WebSocket connection closed.")
        self.pileSize: int = 0
        self.gamePoints: dict[str, int] = {}
        self.gameOver: bool = False
        self.hand: List[int] = []
        self.deck: List[int] = []
        self.myTurn = False
        self.websocket = None

    async def manage_game_tasks(self, websocket):
        receive_task = asyncio.create_task(self.receive_messages(websocket))
        send_task = asyncio.create_task(self.send_messages(websocket))

        try:
            await asyncio.gather(receive_task, send_task)
        except asyncio.CancelledError:
            print("Game tasks were cancelled.")
        finally:
            receive_task.cancel()
            send_task.cancel()
            await asyncio.gather(receive_task, send_task, return_exceptions=True)

    async def receive_messages(self, websocket):
        try:
            while not self.gameOver:
                message = await websocket.recv()
                self.process_update(message)
                self.print_game_update()
                await asyncio.sleep(1)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed.")
        finally:
            print("Receive messages task ended.")

    async def send_messages(self, websocket):
        try:
            while not self.gameOver:
                if self.myTurn:
                    move = input(
                        "Your move: format is [CARD_INDEX] [PLACE 1] [PLACE 2 (if its period card)]:")
                    parts = move.split(' ')
                    cardIndex = int(parts[0])
                    cardPlace = [int(parts[1])] if len(parts) == 2 else [int(parts[1]), int(parts[2])]

                    playerMove = PlayerMove(cardIndex=cardIndex, cardPlaces=cardPlace)
                    playerMoveDict = playerMove.model_dump()
                    await websocket.send(json.dumps(playerMoveDict))
                    self.myTurn = False
                else:
                    await asyncio.sleep(1)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed during send.")
        finally:
            print("Send messages task ended.")

    def process_update(self, message):
        message = json.loads(message)
        self.hand = message["hands"][self.currName]
        self.deck = message["deck"]
        self.gameOver = message["over"]
        self.gamePoints = message["points"]
        self.pileSize = message["pileSize"]
        if message["currentTurn"] == self.currName:
            self.myTurn = True

    def print_game_update(self):
        print("/////////////////////////")
        print("GAME UPDATE!!!!!!")
        print("DECK IS", self.deck)
        print("MY HAND IS", self.hand)
        print("POINTS ARE ", self.gamePoints)
        print(self.pileSize, "CARDS LEFT IN PILE")
        print("/////////////////////////")

    def attemptAuth(self, parts):
        if len(parts) != 3:
            print("Invalid format. Use: LOG [USERNAME] [PASSWORD]")
            return

        usr, pasw = parts[1], parts[2]
        register_data = {
            "userName": usr,
            "password": pasw
        }
        try:
            result = requests.get(f"{self.authAddrs}/tryAuth", json=register_data)
            result = result.json()["message"]
            if result == "SUCCESSFULLY LOGGED IN":
                self.currName = usr
                self.loggedOn = True
                print(result, " HELLO, ", self.currName)
            else:
                print("wrong credentials. sry :(((")
        except requests.exceptions.RequestException as e:
            print(f"Login failed: {str(e)}")

    def attemptRegister(self, parts):
        if len(parts) != 3:
            print("Invalid format. Use: REG [USERNAME] [PASSWORD]")
            return

        usr, pasw = parts[1], parts[2]
        register_data = {
            "userName": usr,
            "password": pasw
        }
        try:
            result = requests.post(f"{self.authAddrs}/tryRegister", json=register_data)
            print("Registration result:", result.json())
        except requests.exceptions.RequestException as e:
            print(f"Registration failed: {str(e)}")

    def cleanup(self):
        print("Cleaning up...")


if __name__ == "__main__":
    client = ClientService()