import sys
import os


from threading import Thread
from time import sleep

import uvicorn
import requests

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'service')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))
from EnqueueRequest import EnqueueRequest
from RegisterAddrRequest import RegisterAddrRequest
from fastapi import FastAPI

from QueueService import QueueService


class QueueAPI:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.queueService = QueueService()
        self.addressStruct = RegisterAddrRequest()
        self.addressStruct.address = f"https://timeline-production-612c.up.railway.app"
        self.gameManagerAddr = ""
        self.register_routes()

        self.worker_thread = Thread(target=self.work, daemon=True)
        self.worker_thread.start()

    def register_routes(self):
        response = requests.post("https://timeline-production-1416.up.railway.app/setQueueAddress", json=self.addressStruct.dict())
        print("RESP FOR SETTING ADDRESS OF QUEUE ", response.json())

        gameManagerResponse = requests.get(f"https://timeline-production-1416.up.railway.app/gameManagerAddress")
        self.gameManagerAddr = f"{gameManagerResponse.json()['message']}"

        @self.app.post("/enqueue")
        async def enterQueue(enqueueRequest: EnqueueRequest):
            try:
                self.queueService.enqueue(enqueueRequest)
                return {"message": "ENQUEUED"}
            except:
                return {"message": "U ARE BANNED"}

        @self.app.post("/dequeue")
        async def enterQueue(enqueueRequest: EnqueueRequest):
            try:
                self.queueService.dequeue(enqueueRequest)
                return {"message": "DEQUEUED"}
            except:
                return {"message": "NOT IN LINE ANYWAY"}

        @self.app.get("/pollForSelf")
        async def pollForSelf(enqueueRequest: EnqueueRequest):
            return {"message": self.queueService.poll(enqueueRequest)}

    def work(self):
        while True:
            print("IS ENOUGH?")
            if self.queueService.checkIfEnough():
                print("YESS")
                gameAddress = requests.get(f"{self.gameManagerAddr}/getServer").json()["message"]
                print("GAME ADDRESS IS", gameAddress)
                if gameAddress == "None":
                    print("NONE AVAILABLE")
                    continue
                print("GET SERVER IS ", gameAddress)
                self.queueService.setGameAddress(gameAddress)
            else:
                print("NAY")


            print(f"WAITING... {len(self.queueService.queue)} PLAYERS IN QUEUE")
            sleep(5)


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 9092))
    app = QueueAPI(host, port).app
    uvicorn.run(app, host=host, port=port)
