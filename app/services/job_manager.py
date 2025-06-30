import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.jobs import PollingJobConfig, PollingJobStatus
from app.services.polling_service import PollingService
from app.core.database import async_session

logger = logging.getLogger(__name__)

class JobManager:
    """Manages background polling jobs"""
    
    def __init__(self):
        self._active_tasks: Dict[str, asyncio.Task] = {}
        self._polling_service = PollingService()
        self._shutdown_event = asyncio.Event()
    
    async def create_polling_job(
        self,
        symbols: list[str],
        interval: int,
        provider: str,
        db: AsyncSession
    ) -> str:
        """
        Create a new polling job and start it
        
        Args:
            symbols: List of stock symbols to poll
            interval: Polling interval in seconds
            provider: Data provider name
            db: Database session
            
        Returns:
            str: Job ID
        """
        try:
            # Create job record
            job_id = str(uuid.uuid4())
            job_config = PollingJobConfig(
                id=job_id,
                symbols=symbols,
                interval=interval,
                provider=provider,
                status=PollingJobStatus.accepted
            )
            
            db.add(job_config)
            await db.commit()
            await db.refresh(job_config)
            
            # Start background task (without passing db session)
            task = asyncio.create_task(
                self._run_polling_job(job_id, symbols, interval, provider),
                name=f"polling_job_{job_id}"
            )
            
            self._active_tasks[job_id] = task
            
            logger.info(f"Created polling job {job_id} for symbols: {symbols}")
            return job_id
            
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating polling job: {e}")
            raise
    
    async def _run_polling_job(
        self,
        job_id: str,
        symbols: list[str],
        interval: int,
        provider: str
    ):
        """
        Run the polling job in background
        
        Args:
            job_id: Job identifier
            symbols: List of stock symbols
            interval: Polling interval in seconds
            provider: Data provider name
        """
        try:
            # Update status to running using session factory
            await self._update_job_status(job_id, PollingJobStatus.running)
            
            while not self._shutdown_event.is_set():
                try:
                    # Poll all symbols using session factory
                    await self._polling_service.poll_symbols(
                        symbols=symbols,
                        provider=provider,
                        job_id=job_id
                    )
                    
                    # Wait for next interval
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=interval
                    )
                    
                except asyncio.TimeoutError:
                    # Continue polling
                    continue
                except Exception as e:
                    logger.error(f"Error in polling job {job_id}: {e}")
                    # Continue despite errors
                    await asyncio.sleep(interval)
            
            # Update status to completed using session factory
            await self._update_job_status(job_id, PollingJobStatus.completed)
            
        except Exception as e:
            logger.error(f"Fatal error in polling job {job_id}: {e}")
            await self._update_job_status(job_id, PollingJobStatus.failed)
        finally:
            # Clean up task reference
            self._active_tasks.pop(job_id, None)
    
    async def stop_job(self, job_id: str, db: AsyncSession) -> bool:
        """
        Stop a running polling job
        
        Args:
            job_id: Job identifier
            db: Database session
            
        Returns:
            bool: True if job was stopped, False if not found
        """
        task = self._active_tasks.get(job_id)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            await self._update_job_status(job_id, PollingJobStatus.completed)
            logger.info(f"Stopped polling job {job_id}")
            return True
        
        return False
    
    async def get_job_status(self, job_id: str, db: AsyncSession) -> Optional[PollingJobConfig]:
        """
        Get job status from database
        
        Args:
            job_id: Job identifier
            db: Database session
            
        Returns:
            PollingJobConfig: Job configuration and status
        """
        result = await db.execute(
            select(PollingJobConfig).where(PollingJobConfig.id == job_id)
        )
        return result.scalar_one_or_none()
    
    async def list_jobs(self, db: AsyncSession) -> list[PollingJobConfig]:
        """
        List all polling jobs
        
        Args:
            db: Database session
            
        Returns:
            list[PollingJobConfig]: List of all job configurations
        """
        result = await db.execute(select(PollingJobConfig))
        return result.scalars().all()
    
    async def _update_job_status(
        self,
        job_id: str,
        status: PollingJobStatus
    ):
        """Update job status in database using session factory"""
        async with async_session() as session:
            try:
                await session.execute(
                    update(PollingJobConfig)
                    .where(PollingJobConfig.id == job_id)
                    .values(status=status)
                )
                await session.commit()
                logger.debug(f"Updated job {job_id} status to {status}")
            except Exception as e:
                await session.rollback()
                logger.error(f"Error updating job status for {job_id}: {e}")
    
    async def shutdown(self):
        """Graceful shutdown - stop all active jobs"""
        logger.info("Shutting down job manager...")
        self._shutdown_event.set()
        
        # Cancel all active tasks
        tasks = list(self._active_tasks.values())
        for task in tasks:
            task.cancel()
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        logger.info("Job manager shutdown complete")

# Global job manager instance
_job_manager: Optional[JobManager] = None

def get_job_manager() -> JobManager:
    """Get global job manager instance"""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager

async def shutdown_job_manager():
    """Shutdown global job manager"""
    global _job_manager
    if _job_manager:
        await _job_manager.shutdown()
        _job_manager = None 