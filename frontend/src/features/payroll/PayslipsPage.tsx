import { ReceiptText } from 'lucide-react';

import { useMyPayslips } from '@/api/payroll';
import { Card } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/display';
import { EmptyState, ErrorState, SectionLoader } from '@/components/ui/feedback';
import { formatMoney, formatMonth } from '@/lib/format';

export function PayslipsPage() {
  const { data, isPending, error, refetch } = useMyPayslips();

  return (
    <>
      <PageHeader title="Payslips" description="Payslips appear here once payroll is finalized." />
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
              { header: 'Month', cell: (row) => <span className="font-medium text-slate-900">{formatMonth(row.month)}</span> },
              { header: 'Working days', cell: (row) => row.working_days, align: 'right' },
              { header: 'Unpaid days', cell: (row) => row.unpaid_days, align: 'right' },
              { header: 'Gross', cell: (row) => formatMoney(row.gross), align: 'right' },
              { header: 'Deductions', cell: (row) => <span className="text-rose-600">−{formatMoney(row.deduction)}</span>, align: 'right' },
              { header: 'Net pay', cell: (row) => <span className="font-semibold text-slate-900">{formatMoney(row.net)}</span>, align: 'right' },
            ]}
            empty={<EmptyState icon={ReceiptText} title="No payslips yet" description="Check back after payroll is finalized." />}
          />
        )}
      </Card>
    </>
  );
}
