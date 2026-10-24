import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { Employee, EmployeeInput, EmployeeUpdate } from '@/types/api';
import { queryKeys } from './keys';

export const useEmployees = () =>
  useQuery({ queryKey: queryKeys.employees, queryFn: () => http.get<Employee[]>('/employees') });

export function useCreateEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: EmployeeInput) => http.post<Employee>('/employees', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.employees });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
    },
  });
}

export function useUpdateEmployee() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, ...input }: EmployeeUpdate & { id: number }) => http.patch<Employee>(`/employees/${id}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.employees });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
    },
  });
}
