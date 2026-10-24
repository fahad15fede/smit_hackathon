const currency = new Intl.NumberFormat('en-PK', { style: 'currency', currency: 'PKR', maximumFractionDigits: 0 });

export const formatMoney = (value: number) => currency.format(value);

/** Parse a YYYY-MM-DD string as a local calendar date (not UTC midnight). */
export function parseDate(value: string): Date {
  const [year, month, day] = value.slice(0, 10).split('-').map(Number);
  return new Date(year, month - 1, day);
}

export const formatDate = (value: string) =>
  parseDate(value).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });

export const formatShortDate = (value: string) =>
  parseDate(value).toLocaleDateString(undefined, { day: 'numeric', month: 'short' });

export const formatTime = (value: string) =>
  new Date(value).toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });

export const formatDateTime = (value: string) =>
  new Date(value).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });

export function formatMonth(value: string): string {
  const [year, month] = value.split('-').map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString(undefined, { month: 'long', year: 'numeric' });
}

export function formatDateRange(start: string, end: string): string {
  return start === end ? formatDate(start) : `${formatShortDate(start)} – ${formatDate(end)}`;
}

export const toIsoDate = (date: Date) =>
  `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;

export const currentMonth = () => toIsoDate(new Date()).slice(0, 7);

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join('');
}

export const titleCase = (value: string) => value.charAt(0).toUpperCase() + value.slice(1);
