/** Formatting helpers shared by the auction views. */

const arsFormatter = new Intl.NumberFormat('es-AR', {
  style: 'currency',
  currency: 'ARS',
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

/** Amounts arrive from the API as decimal strings. */
export function formatArs(value) {
  if (value === null || value === undefined || value === '') return '—';
  return arsFormatter.format(Number(value));
}

/** "3d 4h", "4h 12m", "12m 30s" — coarse up top, precise near the end. */
export function formatCountdown(seconds) {
  if (!seconds || seconds <= 0) return 'Cerrada';

  const days = Math.floor(seconds / 86400);
  const hours = Math.floor((seconds % 86400) / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (days > 0) return `${days}d ${hours}h`;
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m ${String(secs).padStart(2, '0')}s`;
}

/** Under an hour the countdown turns urgent; the last 3 minutes are the anti-snipe window. */
export function urgencyClass(seconds) {
  if (!seconds || seconds <= 0) return 'ended';
  if (seconds <= 180) return 'critical';
  if (seconds <= 3600) return 'urgent';
  return 'normal';
}

export function formatDateTime(iso) {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('es-AR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

/** Value for a `datetime-local` input, in the browser's own timezone. */
export function toLocalInputValue(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const offset = d.getTimezoneOffset() * 60000;
  return new Date(d.getTime() - offset).toISOString().slice(0, 16);
}
