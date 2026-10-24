import { ArrowRight, CalendarDays, ClipboardCheck, Clock, Percent, Plane, ReceiptText, UserCheck, Users, UserX } from 'lucide-react';
import { Link } from 'react-router-dom';

import { useOrganizationDashboard, usePersonalDashboard } from '@/api/insights';
import { StatusBadge } from '@/components/ui/Badge';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { PageHeader, PersonCell, StatCard } from '@/components/ui/display';
import { EmptyState, ErrorState, PageLoader } from '@/components/ui/feedback';
import { CheckInCard } from '@/features/attendance/CheckInCard';
import { useCurrentUser } from '@/features/auth/auth-context';
import { LeaveBalanceList } from '@/features/leave/LeaveBalanceList';
import { formatDate, formatDateRange, formatMoney, formatMonth, parseDate, toIsoDate } from '@/lib/format';
import { isManager } from '@/lib/roles';
import { AttendanceTrendChart } from './AttendanceTrendChart';
import { DashboardSummaryCard } from './DashboardSummaryCard';

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

function OrganizationDashboardView() {
  const { data, isPending, error, refetch } = useOrganizationDashboard();
  if (isPending) return <PageLoader />;
  if (error) return <ErrorState error={error} onRetry={() => refetch()} />;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-6">
        <StatCard label="Active employees" value={data.headcount} icon={Users} tone="slate" />
        <StatCard label="On time" value={data.present} icon={UserCheck} tone="brand" />
        <StatCard label="Late" value={data.late} icon={Clock} tone="amber" />
        <StatCard label="On leave" value={data.on_leave} icon={Plane} tone="sky" />
        <StatCard
          label="Not checked in"
          value={data.absent}
          icon={UserX}
          tone="rose"
          hint={data.is_working_day ? undefined : 'Non-working day'}
        />
        <StatCard
          label="Attendance rate"
          value={data.month_attendance_rate === null ? '—' : `${data.month_attendance_rate}%`}
          icon={Percent}
          tone="violet"
          hint="This month to date"
        />
      </div>

      <DashboardSummaryCard />

      <div className="grid gap-6 xl:grid-cols-5">
        <Card className="xl:col-span-3">
          <CardHeader title="Attendance trend" description="Check-ins over the last 14 days" />
          <CardBody>
            <AttendanceTrendChart data={data.trend} />
          </CardBody>
        </Card>

        <Card className="xl:col-span-2">
          <CardHeader
            title="Awaiting approval"
            description={`${data.pending_leaves} pending leave request${data.pending_leaves === 1 ? '' : 's'}`}
            action={
              <Link to="/approvals" className="inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-800">
                Review <ArrowRight className="size-4" />
              </Link>
            }
          />
          {data.recent_pending.length === 0 ? (
            <EmptyState icon={ClipboardCheck} title="All caught up" description="No leave requests are waiting." />
          ) : (
            <ul className="divide-y divide-slate-100">
              {data.recent_pending.map((leave) => (
                <li key={leave.id} className="flex items-center justify-between gap-3 px-5 py-3.5">
                  <PersonCell name={leave.employee.full_name} subtitle={`${leave.leave_type.name} · ${leave.working_days} day(s)`} />
                  <span className="text-right text-xs text-slate-500">{formatDateRange(leave.start_date, leave.end_date)}</span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>
    </div>
  );
}

function PersonalDashboardView() {
  const { data, isPending, error, refetch } = usePersonalDashboard();
  if (isPending) return <PageLoader />;
  if (error) return <ErrorState error={error} onRetry={() => refetch()} />;

  const payslip = data.latest_payslip;
  return (
    <div className="space-y-6">
      <CheckInCard today={data.today} isWorkingDay={data.is_working_day} record={data.attendance} />

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader
            title="Leave balance"
            description={`Your allowance for ${parseDate(data.today).getFullYear()}`}
            action={
              <Link to="/leave" className="inline-flex items-center gap-1 text-sm font-medium text-brand-700 hover:text-brand-800">
                Request leave <ArrowRight className="size-4" />
              </Link>
            }
          />
          <CardBody>
            <LeaveBalanceList balances={data.balances} />
          </CardBody>
        </Card>

        <div className="space-y-6">
          <StatCard label="Pending requests" value={data.pending_leaves} icon={CalendarDays} tone="amber" />
          <Card>
            <CardHeader title="Latest payslip" />
            <CardBody>
              {payslip ? (
                <div>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-slate-500">{formatMonth(payslip.month)}</p>
                    <StatusBadge status={payslip.status} />
                  </div>
                  <p className="mt-2 text-3xl font-semibold tracking-tight text-slate-900">{formatMoney(payslip.net)}</p>
                  <p className="mt-1 text-xs text-slate-500">
                    Gross {formatMoney(payslip.gross)} · Deductions {formatMoney(payslip.deduction)}
                  </p>
                  <Link to="/payslips" className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-brand-700">
                    All payslips <ArrowRight className="size-4" />
                  </Link>
                </div>
              ) : (
                <EmptyState icon={ReceiptText} title="No payslips yet" className="py-4" />
              )}
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  );
}

export function DashboardPage() {
  const user = useCurrentUser();
  const manager = isManager(user.role);
  return (
    <>
      <PageHeader
        title={`${greeting()}, ${user.employee.full_name.split(' ')[0]}`}
        description={manager ? `Here is how your organization looks today, ${formatDate(toIsoDate(new Date()))}.` : 'Here is your day at a glance.'}
      />
      {manager ? <OrganizationDashboardView /> : <PersonalDashboardView />}
    </>
  );
}
