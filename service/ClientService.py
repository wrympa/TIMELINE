import random
import string
import uuid
import asyncio
from asyncio import sleep
from datetime import datetime

import websockets
import requests
import json
import atexit
from typing import List
from urllib.parse import urlparse

from models.Ping import Ping
from models.PlayerMove import PlayerMove


class ClientService:
    def __init__(self, visual: bool):
        self.currMovePlaces = None
        self.currMoveIndex = None
        self.gameStateDict = None
        self.queueWaitingStatus: str = ""
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
        self.gameAddrs = ""

        # Get service addresses
        self.get_service_addresses()
        atexit.register(self.cleanup)

        # Use asyncio to run the main client loop
        self.visual = visual
        if not self.visual:
            asyncio.run(self.start_client())

    def get_service_addresses(self):
        auth_response = requests.get(f"{self.addressAddr}/authAddress")
        self.authAddrs = f"{auth_response.json()['message']}"
        print(f"Auth address: {self.authAddrs}")

        queue_response = requests.get(f"{self.addressAddr}/queueAddress")
        self.queAddrs = f"{queue_response.json()['message']}"
        print(f"Queue address: {self.queAddrs}")

        self.gameAddrs = ""

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
            await self.awaitQueueResponse()
        else:
            print("SOMETHING WRONG WITH SERVER OR UR BANNED")

    async def awaitQueueResponse(self):
        while True:
            await asyncio.sleep(5)
            self.queueWaitingStatus = "USER IS WAITING"
            enqueue_data = {"UUID": self.currentGameUUID}
            result = requests.get(f"{self.queAddrs}/pollForSelf", json=enqueue_data).json()["message"]
            if result != "Waiting":
                self.gameAddrs = result
                break

        self.queueWaitingStatus = "MATCH FOUND, STARTING GAME"
        await self.connect_to_websocket()
        self.queueWaitingStatus = ""

    async def connect_to_websocket(self):
        parsed_url = urlparse(self.gameAddrs)
        uri = f"ws://{parsed_url.hostname}:{parsed_url.port}/ws/{self.currName}"
        print(uri)

        try:
            async with websockets.connect(uri) as websocket:
                print("Connected to game server!")
                self.websocket = websocket
                self.websocket.close_timeout = 500
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
        self.gameAddrs = ""
        self.gameStateDict = None

    async def manage_game_tasks(self, websocket):
        receive_task = asyncio.create_task(self.receive_messages())
        send_task = asyncio.create_task(self.send_messages())
        keepAlive_task = asyncio.create_task(self.keepPinging())

        try:
            await asyncio.gather(receive_task, send_task, keepAlive_task)
        except asyncio.CancelledError:
            print("Game tasks were cancelled.")
        finally:
            receive_task.cancel()
            send_task.cancel()
            print("CLEANUP")
            await self.postGameCleanUp()

    async def get_user_input(self):
        return await asyncio.to_thread(input,
                                       "Your move: format is [CARD_INDEX] [PLACE 1] [PLACE 2 (if its period card)]:")


    async def receive_messages(self):
        try:
            while not self.gameOver:
                message = await self.websocket.recv()
                self.process_update(message)
                self.print_game_update()
                await asyncio.sleep(1)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed.")
        finally:
            print("Receive messages task ended.")

    async def keepPinging(self):
        while not self.gameOver:
            pingInfo = Ping(sendJi=str(datetime.utcnow().timestamp()))
            pingInfo = pingInfo.model_dump()
            await self.websocket.send(json.dumps(pingInfo))
            await asyncio.sleep(10)

    async def send_messages(self):
        try:
            while not self.gameOver:
                if not self.visual:
                    print("IS MY TURN", self.myTurn)
                    if self.myTurn:
                        move = await self.get_user_input()
                        parts = move.split(' ')
                        cardIndex = int(parts[0])
                        cardPlace = [int(parts[1])] if len(parts) == 2 else [int(parts[1]), int(parts[2])]
                        playerMove = PlayerMove(cardIndex=cardIndex, cardPlaces=cardPlace)
                        playerMoveDict = playerMove.model_dump()
                        await self.websocket.send(json.dumps(playerMoveDict))
                        self.myTurn = False
                    else:
                        await asyncio.sleep(5)
                else:
                    print("CHECK IF NONE", self.currMoveIndex, self.currMovePlaces)
                    if self.currMoveIndex is not None and self.currMovePlaces is not None:
                        playerMove = PlayerMove(cardIndex=self.currMoveIndex, cardPlaces=self.currMovePlaces)
                        playerMoveDict = playerMove.model_dump()
                        print("SENDING")
                        await self.websocket.send(json.dumps(playerMoveDict))
                        print("SENT")
                        self.myTurn = False
                        self.currMovePlaces = None
                        self.currMoveIndex = None
                    else:
                        await asyncio.sleep(5)
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed during send.")
        finally:
            print("Send messages task ended.")

    def recieveMoveFromVisuals(self, cardIndex: int, cardPlaces: List[int]):
        print("AAAAA")
        self.currMoveIndex = cardIndex
        self.currMovePlaces = cardPlaces
        print("SETTO", self.currMoveIndex, self.currMovePlaces)

    def process_update(self, message):
        message = json.loads(message)
        self.gameStateDict = message
        self.hand = message["hands"][self.currName]
        self.deck = message["deck"]
        self.gameOver = message["over"]
        self.gamePoints = message["points"]
        self.pileSize = message["pileSize"]
        print(message["currentTurn"], self.currName)
        if message["currentTurn"] == self.currName:
            self.myTurn = True
            print("MY TURN")

    def print_game_update(self):
        print("/////////////////////////")
        print("GAME UPDATE!!!!!!")
        print("DECK IS", self.deck)
        print("MY HAND IS", self.hand)
        print("POINTS ARE ", self.gamePoints)
        print(self.pileSize, "CARDS LEFT IN PILE")
        print("/////////////////////////")

    def attemptAuth(self, parts) -> bool:
        if len(parts) != 3:
            print("Invalid format. Use: LOG [USERNAME] [PASSWORD]")
            return False

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
                return True
            else:
                print("wrong credentials. sry :(((")
                return False
        except requests.exceptions.RequestException as e:
            print(f"Login failed: {str(e)}")
            return False

    def attemptRegister(self, parts) -> bool:
        if len(parts) != 3:
            print("Invalid format. Use: REG [USERNAME] [PASSWORD]")
            return False

        usr, pasw = parts[1], parts[2]
        register_data = {
            "userName": usr,
            "password": pasw
        }
        try:
            result = requests.post(f"{self.authAddrs}/tryRegister", json=register_data)
            print("Registration result:", result.json())
            if result.json()["message"] == "SUCCESSFULLY REGISTERED":
                return True
        except requests.exceptions.RequestException as e:
            print(f"Registration failed: {str(e)}")
        return False

    def cleanup(self):
        print("Cleaning up...")

    def get_game_state(self):
        return self.gameStateDict


if __name__ == "__main__":
    client = ClientService(False)