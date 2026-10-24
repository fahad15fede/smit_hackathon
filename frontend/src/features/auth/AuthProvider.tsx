import { useQueryClient } from '@tanstack/react-query';
import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react';

import { authApi } from '@/api/auth';
import { setUnauthorizedHandler, tokenStore } from '@/lib/http';
import type { Session, User } from '@/types/api';
import { AuthContext, type AuthContextValue } from './auth-context';

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthContextValue['status']>(() => (tokenStore.get() ? 'loading' : 'anonymous'));

  const signOut = useCallback(() => {
    tokenStore.clear();
    queryClient.clear();
    setUser(null);
    setStatus('anonymous');
  }, [queryClient]);

  const signIn = useCallback((session: Session) => {
    tokenStore.set(session.access_token);
    setUser(session.user);
    setStatus('authenticated');
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(signOut);
    return () => setUnauthorizedHandler(null);
  }, [signOut]);

  // Restore the session from a stored token on first load.
  useEffect(() => {
    if (!tokenStore.get()) return;
    authApi
      .me()
      .then((me) => {
        setUser(me);
        setStatus('authenticated');
      })
      .catch(signOut);
  }, [signOut]);

  const value = useMemo(() => ({ user, status, signIn, signOut }), [user, status, signIn, signOut]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
