class AccountDAO:

    def __init__(self):
        self.accountDict = {"A": "1",
                            "B": "1",
                            "C": "1",
                            "D": "1",
                            }

    def addAccount(self, username, password) -> bool:
        if username in self.accountDict.keys():
            return False
        self.accountDict[username] = password
        return True

    def attemptAuth(self, username, password) -> bool:
        if username not in self.accountDict.keys():
            return False
        return self.accountDict[username] == password
