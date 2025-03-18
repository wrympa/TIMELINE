import os
import sys
from threading import Lock
from typing import List

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models')))
from EnqueueRequest import EnqueueRequest


class QueueService:

    def __init__(self):
        self.queueLock = Lock()
        self.readiesLock = Lock()
        self.queue: List[EnqueueRequest] = []
        self.readies: dict[str, str] = {}

    def enqueue(self, request: EnqueueRequest):
        with self.queueLock:
            self.queue.append(request)
            self.readies[request.UUID] = "Waiting"

    def dequeue(self, request: EnqueueRequest):
        with self.queueLock:
            self.queue.remove(request)
            self.readies.pop(request.UUID, None)

    def poll(self, request: EnqueueRequest) -> dict[str, str]:
        with self.readiesLock:
            currentState = self.readies.get(request.UUID)
            result = currentState
            print("RESULT OF POLL ", result)
            if currentState != "Waiting":
                self.readies.pop(request.UUID, None)
            print("RESULT OF POLL AFTER POP ", result)
            return result

    def checkIfEnough(self) -> bool:
        with self.queueLock:
            return len(self.queue) >= 4

    def setGameAddress(self, gameAddress: str) -> bool:
        trueGameAddress = gameAddress
        first, second, third, fourth = self.queue.pop(), self.queue.pop(), self.queue.pop(), self.queue.pop()

        with self.readiesLock:
            self.readies[first.UUID] = trueGameAddress
            self.readies[second.UUID] = trueGameAddress
            self.readies[third.UUID] = trueGameAddress
            self.readies[fourth.UUID] = trueGameAddress
        print("SET ALL TO ", trueGameAddress)
        return True
