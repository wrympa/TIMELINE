class AddressDAO:

    def __init__(self):
        self.accountDAOAddress = "lel"
        self.queueServiceAddress = "lol"
        self.gameManagerAddress = "lal"

    def getAccDAOAddr(self) -> str:
        return self.accountDAOAddress

    def getQueueServiceAddr(self) -> str:
        return self.queueServiceAddress

    def getGameManagerAddr(self) -> str:
        return self.gameManagerAddress

    def setGameManagerAddr(self, newAddress):
        self.gameManagerAddress = newAddress

    def setAccDAOAddr(self, newAddress):
        self.accountDAOAddress = newAddress

    def setQueueServiceAddr(self,  newAddress):
        self.queueServiceAddress = newAddress
