from fastapi import FastAPI
from app.routers import translate

app = FastAPI(title="askadb - NL to Query")

app.include_router(translate.router, prefix="/translate", tags=["Translate"])
