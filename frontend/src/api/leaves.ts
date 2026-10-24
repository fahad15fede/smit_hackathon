import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { LeaveBalance, LeaveInput, LeaveRequest, LeaveStatus } from '@/types/api';
import { queryKeys } from './keys';

export const useMyLeaves = () =>
  useQuery({ queryKey: queryKeys.leaves.mine, queryFn: () => http.get<LeaveRequest[]>('/leaves/me') });

export const useLeaveBalances = () =>
  useQuery({ queryKey: queryKeys.leaves.balances, queryFn: () => http.get<LeaveBalance[]>('/leaves/me/balances') });

export const useLeaveRequests = (status?: LeaveStatus) =>
  useQuery({
    queryKey: queryKeys.leaves.list(status),
    queryFn: () => http.get<LeaveRequest[]>(status ? `/leaves?status=${status}` : '/leaves'),
  });

function useLeaveMutation<TInput>(mutationFn: (input: TInput) => Promise<LeaveRequest>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.leaves.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
    },
  });
}

export const useRequestLeave = () => useLeaveMutation((input: LeaveInput) => http.post<LeaveRequest>('/leaves', input));

export const useCancelLeave = () =>
  useLeaveMutation((id: number) => http.post<LeaveRequest>(`/leaves/${id}/cancel`));

export const useDecideLeave = () =>
  useLeaveMutation(({ id, ...decision }: { id: number; approved: boolean; comment?: string }) =>
    http.post<LeaveRequest>(`/leaves/${id}/decision`, decision),
  );
