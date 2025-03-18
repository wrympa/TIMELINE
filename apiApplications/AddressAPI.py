import os
import uvicorn
from fastapi import FastAPI
from service.AddressDAO import AddressDAO
from models.RegisterAddrRequest import RegisterAddrRequest


class AddressAPI:
    def __init__(self):
        self.app = FastAPI()
        self.addressDAO = AddressDAO()
        self.register_routes()

    def register_routes(self):
        @self.app.get("/authAddress")
        async def auth_address():
            return {"message": self.addressDAO.getAccDAOAddr()}

        @self.app.get("/queueAddress")
        async def queue_address():
            return {"message": self.addressDAO.getQueueServiceAddr()}

        @self.app.post("/setAuthAddress")
        async def set_auth_address(addressStruct: RegisterAddrRequest):
            self.addressDAO.setAccDAOAddr(addressStruct.address)
            return {"message": "SUCC REGG"}

        @self.app.post("/setQueueAddress")
        async def set_queue_address(addressStruct: RegisterAddrRequest):
            self.addressDAO.setQueueServiceAddr(addressStruct.address)
            return {"message": "SUCC REGG"}

        @self.app.get("/gameManagerAddress")
        async def queue_address():
            return {"message": self.addressDAO.getGameManagerAddr()}

        @self.app.post("/setGameManagerAddress")
        async def set_auth_address(addressStruct: RegisterAddrRequest):
            self.addressDAO.setGameManagerAddr(addressStruct.address)
            return {"message": "SUCC REGG"}


app = AddressAPI().app

if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 9090))
    uvicorn.run(app, host=host, port=port)
