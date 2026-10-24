import { createContext, useContext } from 'react';

import type { Session, User } from '@/types/api';

export interface AuthContextValue {
  user: User | null;
  status: 'loading' | 'authenticated' | 'anonymous';
  signIn: (session: Session) => void;
  signOut: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used inside <AuthProvider>');
  return context;
}

/** For components rendered only behind <RequireAuth>, where a user is guaranteed. */
export function useCurrentUser(): User {
  const { user } = useAuth();
  if (!user) throw new Error('useCurrentUser called without an authenticated user');
  return user;
}
