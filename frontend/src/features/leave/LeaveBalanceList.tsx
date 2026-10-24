import { CalendarDays } from 'lucide-react';

import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/feedback';
import type { LeaveBalance } from '@/types/api';

export function LeaveBalanceList({ balances }: { balances: LeaveBalance[] }) {
  if (balances.length === 0) {
    return (
      <EmptyState
        icon={CalendarDays}
        title="No leave types yet"
        description="Your Admin has not configured any leave types."
        className="py-6"
      />
    );
  }

  return (
    <ul className="grid gap-4 sm:grid-cols-2">
      {balances.map(({ leave_type, used, pending, remaining }) => {
        const quota = Math.max(leave_type.annual_quota, 1);
        return (
          <li key={leave_type.id} className="rounded-lg border border-slate-200 p-4">
            <div className="flex items-center justify-between gap-2">
              <p className="font-medium text-slate-900">{leave_type.name}</p>
              {!leave_type.is_paid && <Badge>Unpaid</Badge>}
            </div>
            <p className="mt-2 text-2xl font-semibold text-slate-900 tabular-nums">
              {remaining}
              <span className="text-sm font-normal text-slate-500"> / {leave_type.annual_quota} days left</span>
            </p>
            <div className="mt-3 flex h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="bg-brand-500" style={{ width: `${(used / quota) * 100}%` }} />
              <div className="bg-amber-400" style={{ width: `${(pending / quota) * 100}%` }} />
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {used} used{pending > 0 && ` · ${pending} pending`}
            </p>
          </li>
        );
      })}
    </ul>
  );
}
