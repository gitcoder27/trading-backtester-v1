import { Play, Clock, CheckCircle, XCircle } from 'lucide-react';

// Centralized status helpers used across multiple views

// Maps a status to a Lucide icon component
export function getStatusIcon(status: string) {
  switch (status) {
    case 'completed':
      return CheckCircle;
    case 'running':
      return Play;
    case 'failed':
      return XCircle;
    default:
      return Clock;
  }
}

// Maps a status to a Badge variant
export function getStatusVariant(
  status: string
): 'success' | 'primary' | 'danger' | 'warning' {
  switch (status) {
    case 'completed':
      return 'success';
    case 'running':
      return 'primary';
    case 'failed':
      return 'danger';
    default:
      return 'warning';
  }
}

