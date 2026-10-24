import type { LeaveStatus } from '@/types/api';

// Hierarchical query keys: invalidating a prefix (e.g. ['leaves']) refreshes every query under it.
export const queryKeys = {
  setup: ['setup'] as const,
  company: ['company'] as const,
  holidays: ['holidays'] as const,
  departments: ['departments'] as const,
  leaveTypes: ['leave-types'] as const,
  employees: ['employees'] as const,
  attendance: {
    all: ['attendance'] as const,
    mine: ['attendance', 'mine'] as const,
    team: (day: string) => ['attendance', 'team', day] as const,
  },
  leaves: {
    all: ['leaves'] as const,
    mine: ['leaves', 'mine'] as const,
    balances: ['leaves', 'balances'] as const,
    list: (status?: LeaveStatus) => ['leaves', 'list', status ?? 'all'] as const,
  },
  payroll: {
    all: ['payroll'] as const,
    run: (id: number) => ['payroll', 'run', id] as const,
  },
  payslips: ['payslips'] as const,
  dashboard: {
    all: ['dashboard'] as const,
    organization: ['dashboard', 'organization'] as const,
    personal: ['dashboard', 'personal'] as const,
  },
  audit: ['audit'] as const,
};
