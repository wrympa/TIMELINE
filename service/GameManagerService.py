from threading import Lock


class GameManagerService:

    def __init__(self):
        self.serverListLock = Lock()
        self.serversList: dict[str, bool] = {}

    def addNewServer(self, address: str):
        with self.serverListLock:
            self.serversList[address] = True

    def isAnyServerFree(self) -> str:
        with self.serverListLock:
            for server in self.serversList.keys():
                if self.serversList[server]:
                    self.serversList[server] = False
                    return server
        return "None"

    def resetServer(self, address: str):
        with self.serverListLock:
            print(address, self.serversList.keys())
            self.serversList[address] = True

