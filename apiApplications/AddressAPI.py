import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import uvicorn

from starlette.responses import JSONResponse

from models.RegisterAddrRequest import RegisterAddrRequest
from service.AddressDAO import AddressDAO
from fastapi import FastAPI


class AddressAPI:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.app = FastAPI()
        self.addressDAO = AddressDAO()
        self.register_routes()

    def register_routes(self):
        @self.app.get("/authAddress")
        async def auth_address():
            print("HERES THE AUTH ADDRESS: ", self.addressDAO.getAccDAOAddr())
            return {"message": self.addressDAO.getAccDAOAddr()}

        @self.app.get("/queueAddress")
        async def queue_address():
            print("HERES THE QUEUE ADDRESS: ", self.addressDAO.getQueueServiceAddr())
            return {"message": self.addressDAO.getQueueServiceAddr()}

        @self.app.post("/setAuthAddress")
        async def set_auth_address(addressStruct: RegisterAddrRequest):
            self.addressDAO.setAccDAOAddr(addressStruct.address)
            print("AUTH ADDRESS IS NOW: ", addressStruct.address)
            return {"message": "SUCC REGG"}

        @self.app.post("/setQueueAddress")
        async def set_queue_address(addressStruct: RegisterAddrRequest):
            self.addressDAO.setQueueServiceAddr(addressStruct.address)
            print("QUEUE ADDRESS IS NOW: ", addressStruct.address)
            return {"message": "SUCC REGG"}

        @self.app.get("/gameManagerAddress")
        async def queue_address():
            print("HERES THE GameManager ADDRESS: ", self.addressDAO.getGameManagerAddr())
            return {"message": self.addressDAO.getGameManagerAddr()}

        @self.app.post("/setGameManagerAddress")
        async def set_auth_address(addressStruct: RegisterAddrRequest):
            self.addressDAO.setGameManagerAddr(addressStruct.address)
            print("GameManager ADDRESS IS NOW: ", addressStruct.address)
            return {"message": "SUCC REGG"}


if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 9090))

    api = AddressAPI(host, port)
    app = api.app
    uvicorn.run(app, host=host, port=port)
