import { Pencil, Plus, Search, Users } from 'lucide-react';
import { useMemo, useState } from 'react';

import { useEmployees } from '@/api/employees';
import { Badge, StatusBadge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { DataTable } from '@/components/ui/DataTable';
import { PageHeader, PersonCell } from '@/components/ui/display';
import { EmptyState, ErrorState, SectionLoader } from '@/components/ui/feedback';
import { Input } from '@/components/ui/form';
import { useCurrentUser } from '@/features/auth/auth-context';
import { formatDate, formatMoney } from '@/lib/format';
import type { Employee } from '@/types/api';
import { EmployeeFormModal } from './EmployeeFormModal';

export function EmployeesPage() {
  const user = useCurrentUser();
  const { data, isPending, error, refetch } = useEmployees();
  const [search, setSearch] = useState('');
  const [modal, setModal] = useState<{ open: boolean; employee: Employee | null }>({ open: false, employee: null });

  const rows = useMemo(() => {
    const term = search.trim().toLowerCase();
    if (!data || !term) return data ?? [];
    return data.filter((employee) =>
      [employee.full_name, employee.email, employee.designation, employee.department?.name ?? '']
        .some((value) => value.toLowerCase().includes(term)),
    );
  }, [data, search]);

  const canEdit = (employee: Employee) => user.role === 'admin' || employee.role !== 'admin';

  return (
    <>
      <PageHeader
        title="Employees"
        description={data ? `${data.filter((e) => e.is_active).length} active of ${data.length} total` : undefined}
        actions={
          <Button icon={Plus} onClick={() => setModal({ open: true, employee: null })}>
            Add employee
          </Button>
        }
      />
      <Card>
        <div className="border-b border-slate-100 p-4">
          <div className="relative max-w-sm">
            <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-slate-400" />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search name, email, designation, department"
              className="pl-9"
            />
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
              { header: 'Name', cell: (row) => <PersonCell name={row.full_name} subtitle={row.email} /> },
              { header: 'Designation', cell: (row) => row.designation },
              { header: 'Department', cell: (row) => row.department?.name ?? <span className="text-slate-400">—</span> },
              { header: 'Role', cell: (row) => <StatusBadge status={row.role} /> },
              { header: 'Joined', cell: (row) => formatDate(row.join_date) },
              { header: 'Salary', cell: (row) => formatMoney(row.monthly_salary), align: 'right' },
              {
                header: 'Status',
                cell: (row) => (row.is_active ? <Badge tone="green">Active</Badge> : <Badge>Inactive</Badge>),
              },
              {
                header: '',
                align: 'right',
                cell: (row) =>
                  canEdit(row) && (
                    <Button
                      size="icon"
                      variant="ghost"
                      icon={Pencil}
                      aria-label={`Edit ${row.full_name}`}
                      onClick={() => setModal({ open: true, employee: row })}
                    />
                  ),
              },
            ]}
            empty={
              <EmptyState
                icon={Users}
                title={search ? 'No matches' : 'No employees yet'}
                description={search ? 'Try a different search term.' : 'Add your first employee to get started.'}
              />
            }
          />
        )}
      </Card>
      <EmployeeFormModal
        open={modal.open}
        employee={modal.employee}
        onClose={() => setModal({ open: false, employee: null })}
      />
    </>
  );
}
