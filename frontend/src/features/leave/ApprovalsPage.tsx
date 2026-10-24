import { Check, ClipboardCheck, X } from 'lucide-react';
import { useState } from 'react';

import { useDecideLeave, useLeaveRequests } from '@/api/leaves';
import { StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { PageHeader, PersonCell, Tabs } from '@/components/ui/display';
import { EmptyState, ErrorState, SectionLoader } from '@/components/ui/feedback';
import { Field, FormError, Textarea } from '@/components/ui/form';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/toast';
import { useCurrentUser } from '@/features/auth/auth-context';
import { formatDateRange, formatDateTime } from '@/lib/format';
import type { LeaveRequest, LeaveStatus } from '@/types/api';

type Filter = LeaveStatus | 'all';

interface Decision {
  leave: LeaveRequest;
  approved: boolean;
}

function DecisionModal({ decision, onClose }: { decision: Decision | null; onClose: () => void }) {
  const toast = useToast();
  const decide = useDecideLeave();
  const [comment, setComment] = useState('');

  const close = () => {
    setComment('');
    decide.reset();
    onClose();
  };

  if (!decision) return null;
  const { leave, approved } = decision;

  const submit = () =>
    decide.mutate(
      { id: leave.id, approved, comment: comment.trim() || undefined },
      {
        onSuccess: () => {
          toast.success(`Leave ${approved ? 'approved' : 'rejected'} for ${leave.employee.full_name}`);
          close();
        },
      },
    );

  return (
    <Modal
      open
      onClose={close}
      title={approved ? 'Approve leave' : 'Reject leave'}
      description={`${leave.employee.full_name} · ${leave.leave_type.name} · ${formatDateRange(leave.start_date, leave.end_date)} (${leave.working_days} day${leave.working_days === 1 ? '' : 's'})`}
      footer={
        <>
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button variant={approved ? 'primary' : 'danger'} loading={decide.isPending} onClick={submit}>
            {approved ? 'Approve' : 'Reject'}
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <FormError message={decide.error?.message} />
        <div className="rounded-lg bg-slate-50 p-4 text-sm text-slate-700">“{leave.reason}”</div>
        <Field label="Comment (optional)" hint="Shared with the employee.">
          <Textarea value={comment} onChange={(event) => setComment(event.target.value)} maxLength={500} />
        </Field>
      </div>
    </Modal>
  );
}

export function ApprovalsPage() {
  const user = useCurrentUser();
  const [filter, setFilter] = useState<Filter>('pending');
  const [decision, setDecision] = useState<Decision | null>(null);
  const { data, isPending, error, refetch } = useLeaveRequests(filter === 'all' ? undefined : filter);
  const pendingCount = useLeaveRequests('pending').data?.length;

  return (
    <>
      <PageHeader title="Leave approvals" description="Review and decide on leave requests from your team." />
      <div className="mb-4">
        <Tabs
          value={filter}
          onChange={setFilter}
          options={[
            { value: 'pending', label: 'Pending', count: pendingCount },
            { value: 'approved', label: 'Approved' },
            { value: 'rejected', label: 'Rejected' },
            { value: 'all', label: 'All' },
          ]}
        />
      </div>
      <Card>
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
              { header: 'Type', cell: (row) => row.leave_type.name },
              { header: 'Dates', cell: (row) => formatDateRange(row.start_date, row.end_date) },
              { header: 'Days', cell: (row) => row.working_days, align: 'right' },
              { header: 'Reason', cell: (row) => <span className="block max-w-56 truncate" title={row.reason}>{row.reason}</span> },
              { header: 'Requested', cell: (row) => <span className="text-slate-500">{formatDateTime(row.created_at)}</span> },
              {
                header: 'Status',
                align: 'right',
                cell: (row) =>
                  row.status === 'pending' && row.employee.id !== user.employee.id ? (
                    <div className="flex justify-end gap-2">
                      <Button size="sm" variant="secondary" icon={X} onClick={() => setDecision({ leave: row, approved: false })}>
                        Reject
                      </Button>
                      <Button size="sm" icon={Check} onClick={() => setDecision({ leave: row, approved: true })}>
                        Approve
                      </Button>
                    </div>
                  ) : (
                    <StatusBadge status={row.status} />
                  ),
              },
            ]}
            empty={
              <EmptyState
                icon={ClipboardCheck}
                title={filter === 'pending' ? 'All caught up' : 'No requests'}
                description={filter === 'pending' ? 'There are no leave requests waiting for review.' : undefined}
              />
            }
          />
        )}
      </Card>
      <DecisionModal decision={decision} onClose={() => setDecision(null)} />
    </>
  );
}
