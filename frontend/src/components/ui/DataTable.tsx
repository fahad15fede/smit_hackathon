import type { ReactNode } from 'react';

import { cn } from '@/lib/cn';

export interface Column<T> {
  header: string;
  cell: (row: T) => ReactNode;
  className?: string;
  align?: 'left' | 'right';
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string | number;
  empty?: ReactNode;
  onRowClick?: (row: T) => void;
}

export function DataTable<T>({ columns, rows, rowKey, empty, onRowClick }: DataTableProps<T>) {
  if (rows.length === 0 && empty) return <>{empty}</>;

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.header}
                scope="col"
                className={cn(
                  'bg-slate-50/80 px-5 py-3 text-xs font-semibold tracking-wide text-slate-500 uppercase',
                  column.align === 'right' ? 'text-right' : 'text-left',
                  column.className,
                )}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick && (() => onRowClick(row))}
              className={cn('transition-colors', onRowClick ? 'cursor-pointer hover:bg-slate-50' : 'hover:bg-slate-50/50')}
            >
              {columns.map((column) => (
                <td
                  key={column.header}
                  className={cn(
                    'px-5 py-3.5 whitespace-nowrap text-slate-700',
                    column.align === 'right' && 'text-right tabular-nums',
                    column.className,
                  )}
                >
                  {column.cell(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
