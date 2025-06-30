from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.market_data import (
    PriceResponse, PollRequest, PollResponse, 
    JobStatus, JobList, JobStopResponse
)
from app.services.providers.factory import provider_dependency
from app.services.providers.base import MarketDataProvider
from app.services.market_data_service import get_market_data_service
from app.services.job_manager import get_job_manager
from app.services.polling_service import PollingService
from app.models.jobs import PollingJobConfig
from app.core.database import get_db

router = APIRouter()

# Route to get the latest price for a given symbol
@router.get("/prices/latest", response_model=PriceResponse)
async def get_latest_price(
    symbol: str,
    provider: MarketDataProvider = Depends(provider_dependency),
    db: AsyncSession = Depends(get_db)
) -> PriceResponse:
    """
    Get the latest price for a given symbol
    """
    try:
        market_data_service = get_market_data_service()
        
        # Check if we have a recent processed price in Redis
        cached_price = await market_data_service.get_latest_processed_price(symbol)
        if cached_price:
            return cached_price
        
        # Fetch fresh data from provider
        price_response, raw_response = await provider.get_latest_price_with_raw_data(symbol)
        
        # Process the data: store raw data and publish to Kafka
        processed_response = await market_data_service.process_price_data(
            symbol=symbol,
            price=price_response.price,
            timestamp=price_response.timestamp,
            provider=price_response.provider,
            raw_response=raw_response,
            db=db
        )
        
        return processed_response
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching price for {symbol}: {e}")

# Route to start polling for prices of given symbols
@router.post("/prices/poll", response_model=PollResponse)
async def start_polling(
    request: PollRequest,
    db: AsyncSession = Depends(get_db)
) -> PollResponse:
    """
    Start polling for prices of given symbols
    """
    try:
        # Validate request parameters
        polling_service = PollingService()
        await polling_service.validate_polling_request(
            symbols=request.symbols,
            interval=request.interval,
            provider=request.provider
        )
        
        # Create and start polling job
        job_manager = get_job_manager()
        job_id = await job_manager.create_polling_job(
            symbols=request.symbols,
            interval=request.interval,
            provider=request.provider,
            db=db
        )
        
        return PollResponse(
            job_id=job_id,
            status="accepted",
            config={
                "symbols": request.symbols,
                "interval": request.interval,
                "provider": request.provider
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error starting polling job: {e}")

# Route to get job status
@router.get("/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> JobStatus:
    """
    Get the status of a polling job
    """
    try:
        job_manager = get_job_manager()
        job = await job_manager.get_job_status(job_id, db)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatus(
            job_id=job.id,
            status=job.status,
            symbols=job.symbols,
            interval=job.interval,
            provider=job.provider,
            created_at=job.created_at.isoformat() if job.created_at else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting job status: {e}")

# Route to list all jobs
@router.get("/jobs", response_model=JobList)
async def list_jobs(
    db: AsyncSession = Depends(get_db)
) -> JobList:
    """
    List all polling jobs
    """
    try:
        job_manager = get_job_manager()
        jobs = await job_manager.list_jobs(db)
        
        job_statuses = [
            JobStatus(
                job_id=job.id,
                status=job.status,
                symbols=job.symbols,
                interval=job.interval,
                provider=job.provider,
                created_at=job.created_at.isoformat() if job.created_at else None
            )
            for job in jobs
        ]
        
        return JobList(jobs=job_statuses)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing jobs: {e}")

# Route to stop/cancel a job
@router.delete("/jobs/{job_id}", response_model=JobStopResponse)
async def stop_job(
    job_id: str,
    db: AsyncSession = Depends(get_db)
) -> JobStopResponse:
    """
    Stop/cancel a polling job
    """
    try:
        job_manager = get_job_manager()
        stopped = await job_manager.stop_job(job_id, db)
        
        if not stopped:
            raise HTTPException(status_code=404, detail="Job not found or already stopped")
        
        return JobStopResponse(message=f"Job {job_id} stopped successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error stopping job: {e}") 