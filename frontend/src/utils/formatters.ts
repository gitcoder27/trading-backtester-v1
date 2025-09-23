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

// Formats trading sessions (days) into a concise duration: `Xd`, `Xmo`, or `Yy`
// - < 60 days  -> days
// - < ~18 months (540 trading days) -> months (approx 21 trading days per month)
// - otherwise -> years (252 trading days per year)
export function formatTradingSessionsDuration(tradingDays: number | undefined | null): string {
  const days = Number(tradingDays ?? 0);
  if (!Number.isFinite(days) || days <= 0) return '—';

  if (days < 60) {
    return `${Math.round(days)}d`;
  }
  const months = days / 21; // approx trading days per month
  if (days < 540) {
    return `${Math.round(months)}mo`;
  }
  const years = days / 252; // approx trading days per year
  const rounded = years >= 10 ? Math.round(years) : Math.round(years * 10) / 10; // 1 decimal for <10y
  return `${rounded}y`;
}

// Returns a Tailwind color class for signed percent strings like "+3.2%" or "-1.0%"
export function getReturnColor(returnStr: string): string {
  if (returnStr === 'N/A') return 'text-gray-400';
  const isPositive = returnStr.startsWith('+');
  return isPositive ? 'text-green-400' : 'text-red-400';
}
