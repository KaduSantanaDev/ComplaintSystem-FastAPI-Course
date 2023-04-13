from fastapi import FastAPI

from db import database
from resources.routes import api_router

app = FastAPI()

app.include_router(api_router)


@app.on_event("startup")
async def startup() -> None:
    if not database.is_connected:
        await database.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    if database.is_connected:
        await database.disconnect()
