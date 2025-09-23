import { useEffect, useRef, useState, useCallback } from 'react';
import { JobService } from '../services/backtest';
import type { Job } from '../types';

interface UseJobPollingOptions {
  onComplete?: (job: Job) => void;
  pollIntervalMs?: number;
  autoStart?: boolean;
}

export function useJobPolling(initialJob: Job, opts: UseJobPollingOptions = {}) {
  const { onComplete, pollIntervalMs = 2000, autoStart = true } = opts;

  const [job, setJob] = useState<Job>(initialJob);
  const [isPolling, setIsPolling] = useState(false);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState<string>('');
  const hasNotifiedRef = useRef<boolean>(
    initialJob.status === 'completed' || initialJob.status === 'failed' || initialJob.status === 'cancelled'
  );
  const intervalRef = useRef<number | null>(null);
  const startTimeRef = useRef<Date>(new Date());

  // Manage auto start/stop based on status and autoStart flag
  const updateEstimatedTime = useCallback((progress: number) => {
    if (progress <= 0) {
      setEstimatedTimeRemaining('Calculating...');
      return;
    }
    const elapsed = Date.now() - startTimeRef.current.getTime();
    const totalEstimated = elapsed / (progress / 100);
    const remaining = totalEstimated - elapsed;
    if (remaining <= 0) {
      setEstimatedTimeRemaining('Completing...');
      return;
    }
    const minutes = Math.floor(remaining / 60000);
    const seconds = Math.floor((remaining % 60000) / 1000);
    setEstimatedTimeRemaining(minutes > 0 ? `~${minutes}m ${seconds}s remaining` : `~${seconds}s remaining`);
  }, []);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const start = useCallback(() => {
    if (intervalRef.current) return;
    setIsPolling(true);
    intervalRef.current = window.setInterval(async () => {
      try {
        const updatedJob = await JobService.getJobStatus(job.id);
        setJob(prev => ({
          ...prev,
          status: updatedJob.status,
          progress: updatedJob.progress || 0,
          error: updatedJob.error,
          completed_at: updatedJob.completed_at
        }));
        updateEstimatedTime(updatedJob.progress || 0);
      } catch (error) {
        if (typeof import.meta !== 'undefined' && import.meta.env?.DEV) {
          console.warn('useJobPolling: polling update failed', error);
        }
      }
    }, pollIntervalMs) as unknown as number;
  }, [job.id, pollIntervalMs, updateEstimatedTime]);

  useEffect(() => {
    const shouldPoll = (job.status === 'running' || job.status === 'pending') && autoStart && !hasNotifiedRef.current;
    if (shouldPoll) start();
    else stop();
    return () => stop();
  }, [job.status, autoStart, start, stop]);

  // Fire onComplete and stop polling on terminal states
  useEffect(() => {
    if (job.status === 'completed' || job.status === 'failed' || job.status === 'cancelled') {
      if (job.status === 'completed' && onComplete && !hasNotifiedRef.current) {
        hasNotifiedRef.current = true;
        onComplete(job);
      }
      stop();
    }
  }, [job.status, onComplete, stop]);

  return {
    job,
    setJob,
    isPolling,
    estimatedTimeRemaining,
    start,
    stop,
  } as const;
}
