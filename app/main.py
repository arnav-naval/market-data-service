from fastapi import FastAPI
from app.api.v1 import router as api_router

app = FastAPI(title="Market-Data-Service", version="0.1.0")
app.include_router(api_router, prefix="/v1")

