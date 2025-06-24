from fastapi import FastAPI
from app.api.v1 import router as api_router
from app.services.kafka_producer import close_kafka_producer

app = FastAPI(title="Market Data Service", version="0.1.0")
app.include_router(api_router, prefix="/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("shutdown")
async def shutdown_event():
    """Graceful shutdown - close Kafka producer"""
    await close_kafka_producer()

