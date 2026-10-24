import { CalendarCheck } from 'lucide-react';
import { useState } from 'react';

import { useMyAttendance, useTeamAttendance } from '@/api/attendance';
import { usePersonalDashboard } from '@/api/insights';
import { StatusBadge } from '@/components/ui/Badge';
import { Card, CardHeader } from '@/components/ui/Card';
import { type Column, DataTable } from '@/components/ui/DataTable';
import { PageHeader, PersonCell, StatCard } from '@/components/ui/display';
import { EmptyState, ErrorState, SectionLoader } from '@/components/ui/feedback';
import { Input } from '@/components/ui/form';
import { formatDate, formatTime, toIsoDate } from '@/lib/format';
import type { AttendanceRecord } from '@/types/api';
import { CheckInCard } from './CheckInCard';

function hoursWorked(record: AttendanceRecord): string {
  if (!record.check_out) return '—';
  const minutes = Math.round((new Date(record.check_out).getTime() - new Date(record.check_in).getTime()) / 60000);
  return `${Math.floor(minutes / 60)}h ${String(minutes % 60).padStart(2, '0')}m`;
}

const TIME_COLUMNS: Column<AttendanceRecord>[] = [
  { header: 'Check in', cell: (row) => formatTime(row.check_in) },
  { header: 'Check out', cell: (row) => (row.check_out ? formatTime(row.check_out) : '—') },
  { header: 'Hours', cell: hoursWorked, align: 'right' },
  { header: 'Status', cell: (row) => <StatusBadge status={row.status} /> },
];

export function MyAttendancePage() {
  const today = usePersonalDashboard();
  const history = useMyAttendance();

  return (
    <>
      <PageHeader title="Attendance" description="Check-in times use the server clock in your company's timezone." />
      <div className="space-y-6">
        {today.data && (
          <CheckInCard today={today.data.today} isWorkingDay={today.data.is_working_day} record={today.data.attendance} />
        )}
        <Card>
          <CardHeader title="History" description="Your most recent attendance records" />
          {history.isPending ? (
            <SectionLoader />
          ) : history.error ? (
            <ErrorState error={history.error} onRetry={() => history.refetch()} />
          ) : (
            <DataTable
              rows={history.data}
              rowKey={(row) => row.id}
              columns={[{ header: 'Date', cell: (row) => formatDate(row.day) }, ...TIME_COLUMNS]}
              empty={<EmptyState icon={CalendarCheck} title="No attendance yet" description="Your check-ins will appear here." />}
            />
          )}
        </Card>
      </div>
    </>
  );
}

export function TeamAttendancePage() {
  const [day, setDay] = useState(() => toIsoDate(new Date()));
  const { data, isPending, error, refetch } = useTeamAttendance(day);
  const late = data?.filter((row) => row.status === 'late').length ?? 0;

  return (
    <>
      <PageHeader
        title="Team attendance"
        description="Who checked in, and when."
        actions={<Input type="date" value={day} max={toIsoDate(new Date())} onChange={(e) => e.target.value && setDay(e.target.value)} className="w-44" />}
      />
      <div className="mb-6 grid grid-cols-2 gap-4 sm:max-w-md">
        <StatCard label="Checked in" value={data?.length ?? '—'} icon={CalendarCheck} />
        <StatCard label="Late" value={data ? late : '—'} icon={CalendarCheck} tone="amber" />
      </div>
      <Card>
        <CardHeader title={formatDate(day)} />
        {isPending ? (
          <SectionLoader />
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : (
          <DataTable
            rows={data}
            rowKey={(row) => row.id}
            columns={[
              { header: 'Employee', cell: (row) => <PersonCell name={row.employee.full_name} subtitle={row.employee.designation} /> },
              ...TIME_COLUMNS,
            ]}
            empty={<EmptyState icon={CalendarCheck} title="No check-ins" description="Nobody checked in on this date." />}
          />
        )}
      </Card>
    </>
  );
}
