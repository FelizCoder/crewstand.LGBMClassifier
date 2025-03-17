import pickle
import uvicorn
from fastapi import FastAPI

from app.services.websocket_service import WebSocketService
from app.utils.config import config
from app.routes.api import api_router
from app.utils.influx_client import InfluxConnector


app = FastAPI(
    version=config.VERSION,
    title=config.PROJECT_NAME,
    debug=config.DEBUG_LEVEL == "DEBUG",
)

influx = InfluxConnector()
lgbm = pickle.load(open("model.pkl", "rb"))
ws_service = WebSocketService(influx=influx, classifier=lgbm)
ws_service.start()

app.include_router(api_router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
