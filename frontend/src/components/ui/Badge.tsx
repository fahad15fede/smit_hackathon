import { Sparkles } from 'lucide-react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';
import { titleCase } from '@/lib/format';
import type { AttendanceStatus, LeaveStatus, PayrollStatus, Role } from '@/types/api';

const TONES = {
  green: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  amber: 'bg-amber-50 text-amber-800 ring-amber-600/20',
  red: 'bg-rose-50 text-rose-700 ring-rose-600/20',
  blue: 'bg-sky-50 text-sky-700 ring-sky-600/20',
  violet: 'bg-violet-50 text-violet-700 ring-violet-600/20',
  slate: 'bg-slate-100 text-slate-600 ring-slate-500/20',
} as const;

export type Tone = keyof typeof TONES;

export function Badge({ tone = 'slate', children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={cn('inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium ring-1 ring-inset', TONES[tone])}
    >
      {children}
    </span>
  );
}

const STATUS_TONES: Record<LeaveStatus | AttendanceStatus | PayrollStatus | Role, Tone> = {
  pending: 'amber',
  approved: 'green',
  rejected: 'red',
  cancelled: 'slate',
  present: 'green',
  late: 'amber',
  draft: 'blue',
  finalized: 'green',
  admin: 'violet',
  hr: 'blue',
  employee: 'slate',
};

export function StatusBadge({ status }: { status: keyof typeof STATUS_TONES }) {
  return <Badge tone={STATUS_TONES[status]}>{status === 'hr' ? 'HR' : titleCase(status)}</Badge>;
}

/** Required on every answer produced by the AI model. */
export function AiBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-md bg-violet-50 px-1.5 py-0.5 text-[11px] font-medium text-violet-700 ring-1 ring-violet-600/20 ring-inset">
      <Sparkles className="size-3" aria-hidden />
      AI-generated
    </span>
  );
}
