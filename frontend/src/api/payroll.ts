import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { PayrollRun, PayrollRunDetail, Payslip } from '@/types/api';
import { queryKeys } from './keys';

export const usePayrollRuns = () =>
  useQuery({ queryKey: queryKeys.payroll.all, queryFn: () => http.get<PayrollRun[]>('/payroll') });

export const usePayrollRun = (id: number | null) =>
  useQuery({
    queryKey: queryKeys.payroll.run(id ?? 0),
    queryFn: () => http.get<PayrollRunDetail>(`/payroll/${id}`),
    enabled: id !== null,
  });

export const useMyPayslips = () =>
  useQuery({ queryKey: queryKeys.payslips, queryFn: () => http.get<Payslip[]>('/payslips/me') });

function usePayrollMutation<TInput, TResult>(mutationFn: (input: TInput) => Promise<TResult>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.payroll.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.payslips });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
    },
  });
}

export const useCreatePayroll = () =>
  usePayrollMutation((month: string) => http.post<PayrollRunDetail>('/payroll', { month }));

export const useFinalizePayroll = () =>
  usePayrollMutation((id: number) => http.post<PayrollRun>(`/payroll/${id}/finalize`));

export const useDeletePayroll = () => usePayrollMutation((id: number) => http.delete(`/payroll/${id}`));
