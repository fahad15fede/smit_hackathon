import { CalendarDays, Plus } from 'lucide-react';
import { useState } from 'react';

import { useCancelLeave, useLeaveBalances, useMyLeaves } from '@/api/leaves';
import { StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/display';
import { EmptyState, ErrorState, SectionLoader } from '@/components/ui/feedback';
import { useToast } from '@/components/ui/toast';
import { formatDateRange } from '@/lib/format';
import type { LeaveDraft } from '@/types/api';
import { LeaveBalanceList } from './LeaveBalanceList';
import { RequestLeaveModal } from './RequestLeaveModal';
import { SmartLeaveInput } from './SmartLeaveInput';

export function LeavePage() {
  const toast = useToast();
  const [requestOpen, setRequestOpen] = useState(false);
  const [draft, setDraft] = useState<LeaveDraft | null>(null);
  const balances = useLeaveBalances();
  const leaves = useMyLeaves();
  const cancelLeave = useCancelLeave();

  const cancel = (id: number) =>
    cancelLeave.mutate(id, { onSuccess: () => toast.success('Leave request cancelled'), onError: toast.error });

  return (
    <>
      <PageHeader
        title="Leave"
        description="Track your balance and request time off."
        actions={
          <Button
            icon={Plus}
            onClick={() => {
              setDraft(null);
              setRequestOpen(true);
            }}
            disabled={!balances.data?.length}
          >
            Request leave
          </Button>
        }
      />
      <div className="space-y-6">
        <Card>
          <CardHeader title="Describe your leave" description="Write it in your own words; we'll fill in the form for you to review." />
          <CardBody>
            <SmartLeaveInput
              disabled={!balances.data?.length}
              onDraft={(parsed) => {
                setDraft(parsed);
                setRequestOpen(true);
              }}
            />
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="Balances" description="Remaining days for this year, including pending requests" />
          <CardBody>
            {balances.isPending ? <SectionLoader /> : <LeaveBalanceList balances={balances.data ?? []} />}
          </CardBody>
        </Card>

        <Card>
          <CardHeader title="My requests" />
          {leaves.isPending ? (
            <SectionLoader />
          ) : leaves.error ? (
            <ErrorState error={leaves.error} onRetry={() => leaves.refetch()} />
          ) : (
            <DataTable
              rows={leaves.data}
              rowKey={(row) => row.id}
              columns={[
                { header: 'Type', cell: (row) => <span className="font-medium text-slate-900">{row.leave_type.name}</span> },
                { header: 'Dates', cell: (row) => formatDateRange(row.start_date, row.end_date) },
                { header: 'Days', cell: (row) => row.working_days, align: 'right' },
                {
                  header: 'Reason',
                  cell: (row) => <span className="block max-w-xs truncate" title={row.reason}>{row.reason}</span>,
                },
                {
                  header: 'Status',
                  cell: (row) => (
                    <div>
                      <StatusBadge status={row.status} />
                      {row.review_comment && <p className="mt-1 max-w-xs truncate text-xs text-slate-500">“{row.review_comment}”</p>}
                    </div>
                  ),
                },
                {
                  header: '',
                  align: 'right',
                  cell: (row) =>
                    row.status === 'pending' && (
                      <Button
                        size="sm"
                        variant="danger-ghost"
                        loading={cancelLeave.isPending && cancelLeave.variables === row.id}
                        onClick={() => cancel(row.id)}
                      >
                        Cancel
                      </Button>
                    ),
                },
              ]}
              empty={
                <EmptyState
                  icon={CalendarDays}
                  title="No leave requests"
                  description="When you request time off it will show up here."
                />
              }
            />
          )}
        </Card>
      </div>
      <RequestLeaveModal
        open={requestOpen}
        onClose={() => setRequestOpen(false)}
        balances={balances.data ?? []}
        draft={draft}
      />
    </>
  );
}
