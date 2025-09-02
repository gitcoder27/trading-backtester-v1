"""
Progress Tracker
Handles backtest progress tracking and database updates
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Make database imports conditional
try:
    from backend.app.database.models import get_session_factory, BacktestJob
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    get_session_factory = None
    BacktestJob = None


class ProgressTracker:
    """
    Handles progress tracking for backtest operations.
    
    This class encapsulates all progress-related functionality,
    providing a clean interface for updating job progress in the database.
    """
    
    def __init__(self, job_id: Optional[int] = None):
        """
        Initialize progress tracker.
        
        Args:
            job_id: Optional job ID for database tracking
        """
        self.job_id = job_id
        self.SessionLocal = get_session_factory() if job_id and DATABASE_AVAILABLE else None
        self._current_progress = 0.0
        self._current_step = "Initialized"
    
    def update(self, progress: float, step: str = None) -> bool:
        """
        Update progress with validation and error handling.
        
        Args:
            progress: Progress value between 0.0 and 1.0
            step: Optional description of current step
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        # Validate progress value
        progress = max(0.0, min(1.0, progress))
        
        # Update internal state
        self._current_progress = progress
        if step:
            self._current_step = step
        
        # Update database if job_id is provided
        if self.job_id and self.SessionLocal:
            return self._update_database(progress, step)
        
        return True
    
    def _update_database(self, progress: float, step: Optional[str]) -> bool:
        """Update progress in database with proper error handling"""
        if not DATABASE_AVAILABLE or not self.SessionLocal:
            logger.debug("Database not available or no session, skipping database update")
            return True
            
        try:
            db = self.SessionLocal()
            try:
                job = db.query(BacktestJob).filter(BacktestJob.id == self.job_id).first()
                if job:
                    job.progress = progress
                    if step:
                        job.current_step = step
                    db.commit()
                    logger.debug(f"Progress updated for job {self.job_id}: {progress:.1%} - {step}")
                    return True
                else:
                    logger.warning(f"Job {self.job_id} not found in database")
                    return False
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Failed to update progress for job {self.job_id}: {e}")
            return False
    
    def start(self, step: str = "Starting backtest") -> bool:
        """Mark backtest as started"""
        return self.update(0.0, step)
    
    def complete(self, step: str = "Backtest completed") -> bool:
        """Mark backtest as completed"""
        return self.update(1.0, step)
    
    def fail(self, error_message: str) -> bool:
        """Mark backtest as failed"""
        return self.update(self._current_progress, f"Error: {error_message}")
    
    @property
    def current_progress(self) -> float:
        """Get current progress value"""
        return self._current_progress
    
    @property
    def current_step(self) -> str:
        """Get current step description"""
        return self._current_step
    
    def get_progress_info(self) -> dict:
        """Get complete progress information"""
        return {
            'job_id': self.job_id,
            'progress': self._current_progress,
            'step': self._current_step,
            'percentage': f"{self._current_progress:.1%}"
        }


class ProgressCallback:
    """
    Legacy callback class for backward compatibility.
    
    This class maintains the original callback interface while
    delegating to the new ProgressTracker internally.
    """
    
    def __init__(self, job_id: int):
        """Initialize with job ID for backward compatibility"""
        self.job_id = job_id
        self.tracker = ProgressTracker(job_id)
    
    def update(self, progress: float, step: str = None):
        """Update progress - maintains original interface"""
        self.tracker.update(progress, step)
