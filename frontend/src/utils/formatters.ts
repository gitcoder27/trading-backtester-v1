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

// Estimate trading days from a date range by approximating 5 trading days per 7-day week
export function estimateTradingDaysFromDates(start?: string, end?: string): number | null {
  if (!start || !end) return null;
  const s = new Date(start);
  const e = new Date(end);
  if (Number.isNaN(s.getTime()) || Number.isNaN(e.getTime())) return null;
  const diffDays = Math.max(0, Math.round((e.getTime() - s.getTime()) / (1000 * 60 * 60 * 24)));
  if (diffDays <= 0) return 0;
  // Approximate trading days; this is a fallback when exact metric isn't provided
  return Math.max(1, Math.round(diffDays * (5 / 7)));
}

// Formats a trading duration given number of trading days into d/m/y units
export function formatTradingDuration(days?: number | null): string {
  if (days == null || Number.isNaN(days)) return 'N/A';
  if (days < 60) return `${days}d`;
  if (days < 365) return `${Math.round(days / 30)}m`;
  return `${(days / 365).toFixed(1)}y`;
}

