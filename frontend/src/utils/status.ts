import { Play, Clock, CheckCircle, XCircle, Square } from 'lucide-react';
import type { JobStatus } from '../types';

// Centralized status helpers used across multiple views

// Maps a status to a Lucide icon component
export function getStatusIcon(status: JobStatus | string) {
  switch (status) {
    case 'completed':
      return CheckCircle;
    case 'running':
      return Play;
    case 'failed':
      return XCircle;
    case 'cancelled':
      return Square;
    default:
      return Clock;
  }
}

// Maps a status to a Badge variant
export function getStatusVariant(
  status: JobStatus | string
): 'success' | 'primary' | 'danger' | 'warning' | 'secondary' {
  switch (status) {
    case 'completed':
      return 'success';
    case 'running':
      return 'primary';
    case 'failed':
      return 'danger';
    case 'cancelled':
      return 'secondary';
    default:
      return 'warning';
  }
}

// Maps a status to a Tailwind text color class for icons
export function getStatusColor(status: JobStatus | string): string {
  switch (status) {
    case 'completed':
      return 'text-green-500';
    case 'running':
      return 'text-blue-500';
    case 'failed':
      return 'text-red-500';
    case 'cancelled':
      return 'text-gray-500';
    case 'pending':
    default:
      return 'text-yellow-500';
  }
}
