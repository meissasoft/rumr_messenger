from fastapi import FastAPI
from app.routers import messenger

app = FastAPI()
app.include_router(messenger.router, prefix="/messenger", tags=["messenger"])