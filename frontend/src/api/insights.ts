import { useQuery } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { AuditEntry, OrganizationDashboard, PersonalDashboard } from '@/types/api';
import { queryKeys } from './keys';

export const useOrganizationDashboard = () =>
  useQuery({
    queryKey: queryKeys.dashboard.organization,
    queryFn: () => http.get<OrganizationDashboard>('/dashboard/organization'),
  });

export const usePersonalDashboard = () =>
  useQuery({ queryKey: queryKeys.dashboard.personal, queryFn: () => http.get<PersonalDashboard>('/dashboard/me') });

export const useAuditLog = () =>
  useQuery({ queryKey: queryKeys.audit, queryFn: () => http.get<AuditEntry[]>('/audit?limit=200') });
