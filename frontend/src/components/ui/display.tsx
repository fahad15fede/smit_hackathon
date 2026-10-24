import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';
import { initials } from '@/lib/format';

export function PageHeader({ title, description, actions }: { title: string; description?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

const STAT_TONES = {
  brand: 'bg-brand-50 text-brand-600',
  amber: 'bg-amber-50 text-amber-600',
  sky: 'bg-sky-50 text-sky-600',
  rose: 'bg-rose-50 text-rose-600',
  violet: 'bg-violet-50 text-violet-600',
  slate: 'bg-slate-100 text-slate-600',
} as const;

interface StatCardProps {
  label: string;
  value: ReactNode;
  icon: LucideIcon;
  tone?: keyof typeof STAT_TONES;
  hint?: string;
}

export function StatCard({ label, value, icon: Icon, tone = 'brand', hint }: StatCardProps) {
  return (
    <div className="rounded-xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <span className={cn('grid size-9 place-items-center rounded-lg', STAT_TONES[tone])}>
          <Icon className="size-[18px]" />
        </span>
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-tight text-slate-900 tabular-nums">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  );
}

const AVATAR_COLORS = [
  'bg-emerald-100 text-emerald-700',
  'bg-sky-100 text-sky-700',
  'bg-violet-100 text-violet-700',
  'bg-amber-100 text-amber-800',
  'bg-rose-100 text-rose-700',
  'bg-teal-100 text-teal-700',
];

export function Avatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' }) {
  const color = AVATAR_COLORS[[...name].reduce((sum, char) => sum + char.charCodeAt(0), 0) % AVATAR_COLORS.length];
  return (
    <span
      className={cn(
        'inline-grid shrink-0 place-items-center rounded-full font-semibold',
        size === 'sm' ? 'size-8 text-xs' : 'size-10 text-sm',
        color,
      )}
      aria-hidden
    >
      {initials(name)}
    </span>
  );
}

export function PersonCell({ name, subtitle }: { name: string; subtitle?: string }) {
  return (
    <div className="flex items-center gap-3">
      <Avatar name={name} size="sm" />
      <div className="min-w-0">
        <p className="truncate font-medium text-slate-900">{name}</p>
        {subtitle && <p className="truncate text-xs text-slate-500">{subtitle}</p>}
      </div>
    </div>
  );
}

interface TabsProps<T extends string> {
  value: T;
  onChange: (value: T) => void;
  options: { value: T; label: string; count?: number }[];
}

export function Tabs<T extends string>({ value, onChange, options }: TabsProps<T>) {
  return (
    <div className="inline-flex rounded-lg bg-slate-100 p-1" role="tablist">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="tab"
          aria-selected={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            'inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
            value === option.value ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700',
          )}
        >
          {option.label}
          {option.count !== undefined && (
            <span className="rounded-full bg-slate-200/80 px-1.5 text-xs text-slate-600 tabular-nums">{option.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}
