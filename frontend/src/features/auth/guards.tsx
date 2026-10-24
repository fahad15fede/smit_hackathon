import type { ReactNode } from 'react';
import { Navigate, useLocation } from 'react-router-dom';

import { useSetupStatus } from '@/api/auth';
import { ErrorState, PageLoader } from '@/components/ui/feedback';
import type { Role } from '@/types/api';
import { useAuth } from './auth-context';

/** Sends visitors to first-run setup when the company does not exist yet. */
export function RequireSetup({ children }: { children: ReactNode }) {
  const setup = useSetupStatus();
  if (setup.isPending) return <PageLoader />;
  if (setup.isError) return <ErrorState error={setup.error} onRetry={() => setup.refetch()} fullScreen />;
  if (!setup.data.ready) return <Navigate to="/setup" replace />;
  return children;
}

export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const location = useLocation();
  if (status === 'loading') return <PageLoader />;
  if (status === 'anonymous') return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}

export function GuestOnly({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  if (status === 'loading') return <PageLoader />;
  if (status === 'authenticated') return <Navigate to="/" replace />;
  return children;
}

export function RequireRole({ roles, children }: { roles: Role[]; children: ReactNode }) {
  const { user } = useAuth();
  if (!user || !roles.includes(user.role)) return <Navigate to="/" replace />;
  return children;
}
