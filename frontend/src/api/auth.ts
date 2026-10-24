import { useMutation, useQuery } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { Session, SetupStatus, User } from '@/types/api';
import { queryKeys } from './keys';

export interface LoginInput {
  email: string;
  password: string;
}

export interface SetupInput extends LoginInput {
  company_name: string;
  admin_name: string;
}

export const authApi = {
  setupStatus: () => http.get<SetupStatus>('/setup/status'),
  setup: (input: SetupInput) => http.post<Session>('/setup', input),
  login: (input: LoginInput) => http.post<Session>('/auth/login', input),
  me: () => http.get<User>('/auth/me'),
  changePassword: (input: { current_password: string; new_password: string }) =>
    http.post<void>('/auth/password', input),
};

export const useSetupStatus = () =>
  useQuery({ queryKey: queryKeys.setup, queryFn: authApi.setupStatus, staleTime: Infinity });

export const useChangePassword = () => useMutation({ mutationFn: authApi.changePassword });
