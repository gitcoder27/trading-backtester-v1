"""
Background job runner for long-running backtests
Uses ThreadPoolExecutor for concurrent processing without Redis dependency
"""

import asyncio
import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, Future
from datetime import datetime
from typing import Dict, Optional, Callable, Any, List
from threading import Lock
import logging

from backend.app.database.models import get_session_factory, BacktestJob, Backtest
from backend.app.services.backtest_service import BacktestService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobStatus:
    """Job status constants"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressCallback:
    """Progress callback for tracking backtest progress"""
    
    def __init__(self, job_id: str, job_runner: 'JobRunner'):
        self.job_id = job_id
        self.job_runner = job_runner
        self.last_update = time.time()
    
    def __call__(self, progress: float, step: str = None, total_steps: int = None):
        """Update job progress"""
        current_time = time.time()
        
        # Throttle updates to avoid too frequent database writes
        if current_time - self.last_update < 1.0:  # Max 1 update per second
            return
        
        self.last_update = current_time
        self.job_runner.update_job_progress(self.job_id, progress, step, total_steps)


class JobRunner:
    """
    Background job runner for backtests
    Manages job execution, progress tracking, and cancellation
    """
    
    def __init__(self, max_workers: int = 2):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_jobs: Dict[str, Future] = {}
        self.cancellation_flags: Dict[str, bool] = {}
        self.lock = Lock()
        self.backtest_service = BacktestService()
        self.SessionLocal = get_session_factory()
    
    def submit_job(
        self,
        job_type: str = "backtest",
        job_data: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[callable] = None,
        # Legacy parameters for backtest compatibility
        strategy: Optional[str] = None,
        strategy_params: Optional[Dict[str, Any]] = None,
        dataset_path: Optional[str] = None,
        csv_bytes: Optional[bytes] = None,
        engine_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit a job for background execution
        Supports both backtest and optimization jobs
        Returns job ID
        """
        if job_type == "backtest":
            # Legacy backtest job
            job_id = self._create_job_record(strategy, strategy_params, dataset_path, engine_options)
            
            # Submit to thread pool
            future = self.executor.submit(
                self._run_backtest_job,
                job_id,
                strategy,
                strategy_params,
                dataset_path,
                csv_bytes,
                engine_options
            )
        
        elif job_type == "optimization":
            # New optimization job
            if not job_data:
                raise ValueError("job_data required for optimization jobs")
            
            job_id = self._create_optimization_job_record(job_data)
            
            # Submit to thread pool
            future = self.executor.submit(
                self._run_optimization_job,
                job_id,
                job_data,
                progress_callback
            )
        
        else:
            raise ValueError(f"Unknown job type: {job_type}")
        
        # Track the job
        with self.lock:
            self.active_jobs[job_id] = future
            self.cancellation_flags[job_id] = False
        
        logger.info(f"Submitted {job_type} job {job_id} for background execution")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a job"""
        db = self.SessionLocal()
        try:
            job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
            if not job:
                return None
            
            return {
                "id": job.id,
                "status": job.status,
                "progress": job.progress,
                "current_step": job.current_step,
                "total_steps": job.total_steps,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "estimated_duration": job.estimated_duration,
                "actual_duration": job.actual_duration,
                "error_message": job.error_message
            }
        finally:
            db.close()
    
    def get_job_results(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get results of a completed job"""
        db = self.SessionLocal()
        try:
            job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
            if not job or job.status != JobStatus.COMPLETED:
                return None
            
            if job.result_data:
                return json.loads(job.result_data)
            return None
        finally:
            db.close()
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        with self.lock:
            if job_id in self.cancellation_flags:
                self.cancellation_flags[job_id] = True
                logger.info(f"Cancellation requested for job {job_id}")
                
                # Update database status
                self._update_job_status(job_id, JobStatus.CANCELLED)
                return True
        return False
    
    def list_jobs(self, limit: int = 50) -> list:
        """List recent jobs"""
        db = self.SessionLocal()
        try:
            jobs = db.query(BacktestJob).order_by(BacktestJob.created_at.desc()).limit(limit).all()
            return [
                {
                    "id": job.id,
                    "status": job.status,
                    "strategy": job.strategy,
                    "progress": job.progress,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None
                }
                for job in jobs
            ]
        finally:
            db.close()
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job from the database"""
        db = self.SessionLocal()
        try:
            job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
            if job:
                # Remove from active jobs if running
                if str(job_id) in self.active_jobs:
                    with self.lock:
                        if str(job_id) in self.active_jobs:
                            del self.active_jobs[str(job_id)]
                        if str(job_id) in self.cancellation_flags:
                            del self.cancellation_flags[str(job_id)]
                
                # Delete from database
                db.delete(job)
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete job {job_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def update_job_progress(self, job_id: str, progress: float, step: str = None, total_steps: int = None):
        """Update job progress in database"""
        db = self.SessionLocal()
        try:
            job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
            if job:
                job.progress = min(1.0, max(0.0, progress))
                if step:
                    job.current_step = step
                if total_steps:
                    job.total_steps = total_steps
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update progress for job {job_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _create_job_record(
        self,
        strategy: str,
        strategy_params: Dict[str, Any],
        dataset_path: Optional[str],
        engine_options: Dict[str, Any]
    ) -> str:
        """Create initial job record in database"""
        db = self.SessionLocal()
        try:
            job = BacktestJob(
                strategy=strategy,
                strategy_params=strategy_params,
                engine_options=engine_options or {},
                dataset_path=dataset_path,
                status=JobStatus.PENDING
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            return str(job.id)
        finally:
            db.close()
    
    def _update_job_status(self, job_id: str, status: str, error_message: str = None, result_data: str = None):
        """Update job status in database"""
        db = self.SessionLocal()
        try:
            job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
            if job:
                job.status = status
                if error_message:
                    job.error_message = error_message
                if result_data:
                    job.result_data = result_data
                
                if status == JobStatus.RUNNING and not job.started_at:
                    job.started_at = datetime.utcnow()
                elif status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                    job.completed_at = datetime.utcnow()
                    if job.started_at:
                        job.actual_duration = (job.completed_at - job.started_at).total_seconds()
                
                db.commit()
        except Exception as e:
            logger.error(f"Failed to update status for job {job_id}: {e}")
            db.rollback()
        finally:
            db.close()
    
    def _create_backtest_record(
        self, 
        strategy: str, 
        strategy_params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> Optional[int]:
        """Create a backtest record in the database"""
        logger.info(f"Creating backtest record for strategy: {strategy}")
        logger.info(f"Result keys: {list(result.keys()) if result else 'None'}")
        
        db = self.SessionLocal()
        try:
            backtest = Backtest(
                strategy_name=strategy,
                strategy_params=strategy_params,
                dataset_id=None,  # We could enhance this later to link to datasets
                status="completed",
                results=result,
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            logger.info(f"About to save backtest record to database")
            db.add(backtest)
            db.commit()
            db.refresh(backtest)
            
            logger.info(f"Successfully created backtest record with ID: {backtest.id}")
            return backtest.id
            
        except Exception as e:
            logger.error(f"Failed to create backtest record: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            db.rollback()
            return None
        finally:
            db.close()
    
    def _is_cancelled(self, job_id: str) -> bool:
        """Check if job has been cancelled"""
        with self.lock:
            return self.cancellation_flags.get(job_id, False)
    
    def _run_backtest_job(
        self,
        job_id: str,
        strategy: str,
        strategy_params: Dict[str, Any],
        dataset_path: Optional[str],
        csv_bytes: Optional[bytes],
        engine_options: Dict[str, Any]
    ):
        """
        Run backtest job in background thread
        This is the main execution function that runs in the thread pool
        """
        logger.info(f"Starting execution of job {job_id}")
        
        try:
            # Update status to running
            self._update_job_status(job_id, JobStatus.RUNNING)
            
            # Create progress callback
            progress_callback = ProgressCallback(job_id, self)
            
            # Simulate initial progress steps
            progress_callback(0.1, "Loading strategy", 5)
            
            # Check for cancellation
            if self._is_cancelled(job_id):
                logger.info(f"Job {job_id} was cancelled during initialization")
                return
            
            # Load data
            progress_callback(0.2, "Loading data", 5)
            
            # Check for cancellation
            if self._is_cancelled(job_id):
                logger.info(f"Job {job_id} was cancelled during data loading")
                return
            
            # Run the actual backtest with enhanced service
            progress_callback(0.3, "Running backtest", 5)
            
            result = self.backtest_service.run_backtest(
                strategy=strategy,
                strategy_params=strategy_params,
                dataset_path=dataset_path,
                engine_options=engine_options,
                progress_callback=lambda p, s: progress_callback(0.3 + (p * 0.5), s),  # Scale progress from 0.3 to 0.8
            )
            
            # Check for cancellation one more time
            if self._is_cancelled(job_id):
                logger.info(f"Job {job_id} was cancelled after backtest completion")
                return
            
            # Finalize
            progress_callback(0.9, "Finalizing results", 5)
            
            # Create backtest record in the database if backtest was successful
            if result.get('success', False):
                backtest_id = self._create_backtest_record(
                    strategy=strategy,
                    strategy_params=strategy_params,
                    result=result.get('result', {})
                )
                logger.info(f"Created backtest record {backtest_id} for job {job_id}")
            
            # Store results
            result_json = json.dumps(result)
            self._update_job_status(job_id, JobStatus.COMPLETED, result_data=result_json)
            
            # Ensure final progress is set to 1.0
            self.update_job_progress(job_id, 1.0, "Completed", 5)
            logger.info(f"Job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed with error: {e}")
            logger.error(traceback.format_exc())
            self._update_job_status(job_id, JobStatus.FAILED, error_message=str(e))
            
        finally:
            # Clean up
            with self.lock:
                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]
                if job_id in self.cancellation_flags:
                    del self.cancellation_flags[job_id]
    
    def _create_optimization_job_record(self, job_data: Dict[str, Any]) -> str:
        """Create a database record for optimization job"""
        import uuid
        job_id = str(uuid.uuid4())
        
        db = self.SessionLocal()
        try:
            job = BacktestJob(
                id=job_id,
                status=JobStatus.PENDING.value,
                strategy="optimization",  # Mark as optimization job
                strategy_params=job_data.get('param_ranges', {}),
                engine_options=job_data.get('engine_options', {}),
                dataset_path=f"dataset_id_{job_data.get('dataset_id')}",
                total_steps=job_data.get('total_combinations', 1),
                estimated_duration=job_data.get('total_combinations', 1) * 5  # 5 seconds per combination estimate
            )
            db.add(job)
            db.commit()
            logger.info(f"Created optimization job record {job_id}")
            return job_id
        finally:
            db.close()
    
    def _run_optimization_job(self, job_id: str, job_data: Dict[str, Any], progress_callback=None):
        """Run optimization job in background"""
        try:
            self._update_job_status(job_id, JobStatus.RUNNING)
            
            # Import here to avoid circular imports
            from backend.app.services.optimization_service import OptimizationService
            
            optimization_service = OptimizationService()
            
            # Create progress callback that updates job status
            def update_progress(completed: int, total: int):
                progress_pct = completed / total if total > 0 else 0
                self.update_job_progress(
                    job_id, 
                    progress_pct, 
                    f"Completed {completed}/{total} backtests",
                    total
                )
                
                # Check for cancellation
                if self.is_cancelled(job_id):
                    raise Exception("Job was cancelled")
                
                if progress_callback:
                    return progress_callback(completed, total)
            
            # Run the optimization
            result = optimization_service.run_optimization(job_data, update_progress)
            
            if result['success']:
                # Store results in job record
                self._store_job_results(job_id, result)
                self._update_job_status(job_id, JobStatus.COMPLETED)
            else:
                self._update_job_status(job_id, JobStatus.FAILED, error_message=result.get('error', 'Unknown error'))
            
            # Ensure final progress is set to 1.0
            self.update_job_progress(job_id, 1.0, "Optimization completed", job_data.get('total_combinations', 1))
            logger.info(f"Optimization job {job_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Optimization job {job_id} failed with error: {e}")
            logger.error(traceback.format_exc())
            self._update_job_status(job_id, JobStatus.FAILED, error_message=str(e))
            
        finally:
            # Clean up
            with self.lock:
                if job_id in self.active_jobs:
                    del self.active_jobs[job_id]
                if job_id in self.cancellation_flags:
                    del self.cancellation_flags[job_id]
    
    def list_jobs(self, job_type: Optional[str] = None, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """List jobs with optional filtering"""
        db = self.SessionLocal()
        try:
            query = db.query(BacktestJob)
            
            if job_type == "optimization":
                query = query.filter(BacktestJob.strategy == "optimization")
            elif job_type == "backtest":
                query = query.filter(BacktestJob.strategy != "optimization")
            
            if status:
                query = query.filter(BacktestJob.status == status)
            
            jobs = query.order_by(BacktestJob.created_at.desc()).offset(offset).limit(limit).all()
            
            return [{
                "id": job.id,
                "status": job.status,
                "strategy": job.strategy,
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "progress": job.progress,
                "error_message": job.error_message
            } for job in jobs]
        finally:
            db.close()
    
    def get_job_stats(self, job_type: Optional[str] = None) -> Dict[str, Any]:
        """Get job statistics"""
        db = self.SessionLocal()
        try:
            query = db.query(BacktestJob)
            
            if job_type == "optimization":
                query = query.filter(BacktestJob.strategy == "optimization")
            elif job_type == "backtest":
                query = query.filter(BacktestJob.strategy != "optimization")
            
            from sqlalchemy import func
            
            stats = db.query(
                BacktestJob.status,
                func.count(BacktestJob.id).label('count')
            ).filter(
                query.whereclause if query.whereclause is not None else True
            ).group_by(BacktestJob.status).all()
            
            status_counts = {stat.status: stat.count for stat in stats}
            
            # Calculate average completion time for completed jobs
            completed_jobs = query.filter(
                BacktestJob.status == JobStatus.COMPLETED.value,
                BacktestJob.actual_duration.isnot(None)
            ).all()
            
            avg_duration = 0
            if completed_jobs:
                avg_duration = sum(job.actual_duration for job in completed_jobs) / len(completed_jobs)
            
            return {
                'status_counts': status_counts,
                'total_jobs': sum(status_counts.values()),
                'average_completion_time_seconds': avg_duration
            }
        finally:
            db.close()
    
    def shutdown(self):
        """Shutdown the job runner"""
        logger.info("Shutting down job runner...")
        self.executor.shutdown(wait=True)


# Global job runner instance
_job_runner: Optional[JobRunner] = None

def get_job_runner() -> JobRunner:
    """Get the global job runner instance"""
    global _job_runner
    if _job_runner is None:
        _job_runner = JobRunner()
    return _job_runner

def shutdown_job_runner():
    """Shutdown the global job runner"""
    global _job_runner
    if _job_runner:
        _job_runner.shutdown()
        _job_runner = None
