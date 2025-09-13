// Generic formatting helpers used across the app

// Formats duration between two ISO date strings as `Hh Mm` or `Mm`
export function formatDuration(startTime: string, endTime: string): string {
  const start = new Date(startTime);
  const end = new Date(endTime);
  const duration = end.getTime() - start.getTime();

  const hours = Math.floor(duration / (1000 * 60 * 60));
  const minutes = Math.floor((duration % (1000 * 60 * 60)) / (1000 * 60));

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

// Returns a Tailwind color class for signed percent strings like "+3.2%" or "-1.0%"
export function getReturnColor(returnStr: string): string {
  if (returnStr === 'N/A') return 'text-gray-400';
  const isPositive = returnStr.startsWith('+');
  return isPositive ? 'text-green-400' : 'text-red-400';
}

