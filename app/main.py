from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.v1 import router as api_router
from app.services.kafka_producer import close_kafka_producer
from app.services.job_manager import shutdown_job_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    yield
    # Shutdown
    await close_kafka_producer()
    await shutdown_job_manager()


app = FastAPI(title="Market Data Service", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

