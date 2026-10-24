import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { Company, Department, Holiday, LeaveType } from '@/types/api';
import { queryKeys } from './keys';

export type CompanyUpdate = Partial<Omit<Company, 'id'>>;

export const useCompany = () => useQuery({ queryKey: queryKeys.company, queryFn: () => http.get<Company>('/company') });

export function useUpdateCompany() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CompanyUpdate) => http.patch<Company>('/company', input),
    onSuccess: (company) => {
      queryClient.setQueryData(queryKeys.company, company);
      queryClient.invalidateQueries({ queryKey: queryKeys.setup });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
    },
  });
}

export const useHolidays = () =>
  useQuery({ queryKey: queryKeys.holidays, queryFn: () => http.get<Holiday[]>('/holidays') });

export function useAddHoliday() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: Omit<Holiday, 'id'>) => http.post<Holiday>('/holidays', input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.holidays }),
  });
}

export function useDeleteHoliday() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => http.delete(`/holidays/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.holidays }),
  });
}

export const useDepartments = () =>
  useQuery({ queryKey: queryKeys.departments, queryFn: () => http.get<Department[]>('/departments') });

export function useAddDepartment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: { name: string }) => http.post<Department>('/departments', input),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.departments }),
  });
}

export const useLeaveTypes = () =>
  useQuery({ queryKey: queryKeys.leaveTypes, queryFn: () => http.get<LeaveType[]>('/leave-types') });

export function useAddLeaveType() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: Omit<LeaveType, 'id'>) => http.post<LeaveType>('/leave-types', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.leaveTypes });
      queryClient.invalidateQueries({ queryKey: queryKeys.leaves.balances });
    },
  });
}
