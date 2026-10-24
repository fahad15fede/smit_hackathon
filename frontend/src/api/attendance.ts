import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { AttendanceRecord } from '@/types/api';
import { queryKeys } from './keys';

export const useMyAttendance = () =>
  useQuery({ queryKey: queryKeys.attendance.mine, queryFn: () => http.get<AttendanceRecord[]>('/attendance/me') });

export const useTeamAttendance = (day: string) =>
  useQuery({
    queryKey: queryKeys.attendance.team(day),
    queryFn: () => http.get<AttendanceRecord[]>(`/attendance?start=${day}&end=${day}`),
  });

function useAttendanceAction(path: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => http.post<AttendanceRecord>(path),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.attendance.all });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard.all });
    },
  });
}

export const useCheckIn = () => useAttendanceAction('/attendance/check-in');
export const useCheckOut = () => useAttendanceAction('/attendance/check-out');
