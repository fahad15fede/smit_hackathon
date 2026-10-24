import type { Role } from '@/types/api';

export const ROLE_LABELS: Record<Role, string> = {
  admin: 'Admin',
  hr: 'HR',
  employee: 'Employee',
};

export const isManager = (role: Role) => role === 'admin' || role === 'hr';
