import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from db import database
from resources.routes import api_router


origins = [
    "http://localhost",
    "http://localhost:4200"
]


app = FastAPI()
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.on_event("startup")
async def startup() -> None:
    if not database.is_connected:
        await database.connect()


@app.on_event("shutdown")
async def shutdown() -> None:
    if database.is_connected:
        await database.disconnect()



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)