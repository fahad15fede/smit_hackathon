import { useMutation } from '@tanstack/react-query';

import { http } from '@/lib/http';
import type { ChatResponse, ChatTurn, DashboardSummary, LeaveDraftResponse } from '@/types/api';

// AI calls go to our backend only; the browser never talks to the AI provider.

export const useAiChat = () =>
  useMutation({
    mutationFn: (input: { message: string; history: ChatTurn[] }) => http.post<ChatResponse>('/ai/chat', input),
  });

export const useDashboardSummary = () => useMutation({ mutationFn: () => http.post<DashboardSummary>('/ai/summary') });

export const useLeaveDraft = () =>
  useMutation({ mutationFn: (text: string) => http.post<LeaveDraftResponse>('/ai/leave-draft', { text }) });
