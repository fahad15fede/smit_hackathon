import { CheckCircle2, Plus, Trash2, Wallet } from 'lucide-react';
import { useState } from 'react';

import { useCreatePayroll, useDeletePayroll, useFinalizePayroll, usePayrollRun, usePayrollRuns } from '@/api/payroll';
import { StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { PageHeader, PersonCell, StatCard } from '@/components/ui/display';
import { EmptyState, ErrorState, SectionLoader } from '@/components/ui/feedback';
import { Field, FormError, Input } from '@/components/ui/form';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/toast';
import { useCurrentUser } from '@/features/auth/auth-context';
import { currentMonth, formatDateTime, formatMoney, formatMonth } from '@/lib/format';

function CreatePayrollModal({ open, onClose, onCreated }: { open: boolean; onClose: () => void; onCreated: (id: number) => void }) {
  const toast = useToast();
  const createPayroll = useCreatePayroll();
  const [month, setMonth] = useState(currentMonth);

  const close = () => {
    createPayroll.reset();
    onClose();
  };

  const submit = () =>
    createPayroll.mutate(month, {
      onSuccess: (run) => {
        toast.success(`Draft payroll created for ${formatMonth(run.month)}`);
        close();
        onCreated(run.id);
      },
    });

  return (
    <Modal
      open={open}
      onClose={close}
      title="Run payroll"
      description="Creates a draft you can review before an Admin finalizes it."
      footer={
        <>
          <Button variant="secondary" onClick={close}>
            Cancel
          </Button>
          <Button loading={createPayroll.isPending} onClick={submit} disabled={!month}>
            Create draft
          </Button>
        </>
      }
    >
      <div className="space-y-4">
        <FormError message={createPayroll.error?.message} />
        <Field
          label="Payroll month"
          hint="Working days without attendance or approved paid leave are deducted, as is approved unpaid leave."
        >
          <Input type="month" value={month} max={currentMonth()} onChange={(event) => setMonth(event.target.value)} />
        </Field>
      </div>
    </Modal>
  );
}

function PayrollRunModal({ runId, onClose }: { runId: number | null; onClose: () => void }) {
  const user = useCurrentUser();
  const toast = useToast();
  const { data: run, isPending, error } = usePayrollRun(runId);
  const finalize = useFinalizePayroll();
  const remove = useDeletePayroll();

  if (runId === null) return null;
  const isDraft = run?.status === 'draft';

  return (
    <Modal
      open
      onClose={onClose}
      size="xl"
      title={run ? `Payroll · ${formatMonth(run.month)}` : 'Payroll'}
      description={run ? `${run.employee_count} payslip(s) · created ${formatDateTime(run.created_at)}` : undefined}
      footer={
        isDraft && (
          <>
            {user.role === 'hr' && (
              <Button
                variant="danger-ghost"
                icon={Trash2}
                loading={remove.isPending}
                onClick={() =>
                  remove.mutate(run.id, {
                    onSuccess: () => {
                      toast.success('Draft deleted');
                      onClose();
                    },
                    onError: toast.error,
                  })
                }
              >
                Delete draft
              </Button>
            )}
            {user.role === 'admin' ? (
              <Button
                icon={CheckCircle2}
                loading={finalize.isPending}
                onClick={() =>
                  finalize.mutate(run.id, {
                    onSuccess: () => toast.success('Payroll finalized. Payslips are now visible to employees.'),
                    onError: toast.error,
                  })
                }
              >
                Finalize payroll
              </Button>
            ) : (
              <p className="self-center text-sm text-slate-500">An Admin must finalize this payroll.</p>
            )}
          </>
        )
      }
    >
      {isPending ? (
        <SectionLoader />
      ) : error ? (
        <ErrorState error={error} />
      ) : (
        <div className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard label="Gross" value={formatMoney(run.total_gross)} icon={Wallet} tone="slate" />
            <StatCard label="Deductions" value={formatMoney(run.total_deduction)} icon={Wallet} tone="rose" />
            <StatCard label="Net payout" value={formatMoney(run.total_net)} icon={Wallet} />
          </div>
          <div className="overflow-hidden rounded-xl ring-1 ring-slate-200">
            <DataTable
              rows={run.payslips}
              rowKey={(row) => row.id}
              columns={[
                { header: 'Employee', cell: (row) => <PersonCell name={row.employee.full_name} subtitle={row.employee.designation} /> },
                { header: 'Unpaid days', cell: (row) => `${row.unpaid_days} / ${row.working_days}`, align: 'right' },
                { header: 'Gross', cell: (row) => formatMoney(row.gross), align: 'right' },
                { header: 'Deduction', cell: (row) => formatMoney(row.deduction), align: 'right' },
                { header: 'Net', cell: (row) => <span className="font-semibold text-slate-900">{formatMoney(row.net)}</span>, align: 'right' },
              ]}
              empty={<EmptyState icon={Wallet} title="No payslips" description="No active employees with a salary." />}
            />
          </div>
        </div>
      )}
    </Modal>
  );
}

export function PayrollPage() {
  const user = useCurrentUser();
  const { data, isPending, error, refetch } = usePayrollRuns();
  const [createOpen, setCreateOpen] = useState(false);
  const [selectedRun, setSelectedRun] = useState<number | null>(null);

  return (
    <>
      <PageHeader
        title="Payroll"
        description={user.role === 'hr' ? 'Draft monthly payroll for Admin approval.' : 'Review and finalize payroll drafted by HR.'}
        actions={
          user.role === 'hr' && (
            <Button icon={Plus} onClick={() => setCreateOpen(true)}>
              Run payroll
            </Button>
          )
        }
      />
      <Card>
        <CardHeader title="Payroll runs" description="Select a run to see its payslips." />
        {isPending ? (
          <SectionLoader />
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : (
          <DataTable
            rows={data}
            rowKey={(row) => row.id}
            onRowClick={(row) => setSelectedRun(row.id)}
            columns={[
              { header: 'Month', cell: (row) => <span className="font-medium text-slate-900">{formatMonth(row.month)}</span> },
              { header: 'Status', cell: (row) => <StatusBadge status={row.status} /> },
              { header: 'Employees', cell: (row) => row.employee_count, align: 'right' },
              { header: 'Gross', cell: (row) => formatMoney(row.total_gross), align: 'right' },
              { header: 'Deductions', cell: (row) => formatMoney(row.total_deduction), align: 'right' },
              { header: 'Net payout', cell: (row) => <span className="font-semibold text-slate-900">{formatMoney(row.total_net)}</span>, align: 'right' },
            ]}
            empty={
              <EmptyState
                icon={Wallet}
                title="No payroll runs yet"
                description={user.role === 'hr' ? 'Run payroll to create your first draft.' : 'HR has not drafted any payroll yet.'}
              />
            }
          />
        )}
      </Card>
      <CreatePayrollModal open={createOpen} onClose={() => setCreateOpen(false)} onCreated={setSelectedRun} />
      <PayrollRunModal runId={selectedRun} onClose={() => setSelectedRun(null)} />
    </>
  );
}
