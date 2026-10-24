import { ScrollText, Search } from 'lucide-react';
import { useMemo, useState } from 'react';

import { useAuditLog } from '@/api/insights';
import { Badge, type Tone } from '@/components/ui/Badge';
import { Card } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/display';
import { EmptyState, ErrorState, SectionLoader } from '@/components/ui/feedback';
import { Input } from '@/components/ui/form';
import { formatDateTime } from '@/lib/format';

const DOMAIN_TONES: Record<string, Tone> = {
  company: 'violet',
  employee: 'blue',
  attendance: 'green',
  leave: 'amber',
  payroll: 'green',
  password: 'red',
  assistant: 'slate',
};

export function AuditPage() {
  const { data, isPending, error, refetch } = useAuditLog();
  const [search, setSearch] = useState('');

  const rows = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!data || !term) return data ?? [];
    return data.filter((entry) =>
      [entry.action, entry.detail, entry.actor?.email ?? 'system'].some((value) => value.toLowerCase().includes(term)),
    );
  }, [data, search]);

  return (
    <>
      <PageHeader title="Audit log" description="Every change made in HCM Lite, newest first (last 200 events)." />
      <Card>
        <div className="border-b border-slate-100 p-4">
          <div className="relative max-w-sm">
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
            <Input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Filter events" className="pl-9" />
          </div>
        </div>
        {isPending ? (
          <SectionLoader />
        ) : error ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : (
          <DataTable
            rows={rows}
            rowKey={(row) => row.id}
            columns={[
              { header: 'When', cell: (row) => <span className="text-slate-500">{formatDateTime(row.created_at)}</span> },
              {
                header: 'Action',
                cell: (row) => <Badge tone={DOMAIN_TONES[row.action.split('.')[0]] ?? 'slate'}>{row.action}</Badge>,
              },
              { header: 'Detail', cell: (row) => <span className="block max-w-md truncate" title={row.detail}>{row.detail}</span> },
              { header: 'By', cell: (row) => row.actor?.email ?? <span className="text-slate-400">System</span> },
            ]}
            empty={<EmptyState icon={ScrollText} title="No events" />}
          />
        )}
      </Card>
    </>
  );
}
