import os

import uvicorn

from apiApplications.AddressAPI import AddressAPI

app = AddressAPI().app
if __name__ == "__main__":
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 9090))
    uvicorn.run(app, host=host, port=port)
