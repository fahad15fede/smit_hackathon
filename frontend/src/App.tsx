import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Compass } from 'lucide-react';
import { type ComponentType, lazy, type ReactNode } from 'react';
import { BrowserRouter, Link, Route, Routes } from 'react-router-dom';

import { AppLayout } from '@/components/layout/AppLayout';
import { EmptyState } from '@/components/ui/feedback';
import { ToastProvider } from '@/components/ui/toast';
import { AuthProvider } from '@/features/auth/AuthProvider';
import { GuestOnly, RequireAuth, RequireRole, RequireSetup } from '@/features/auth/guards';
import { LoginPage } from '@/features/auth/LoginPage';
import { SetupPage } from '@/features/auth/SetupPage';
import { ApiError } from '@/lib/http';
import type { Role } from '@/types/api';

// Feature pages are code-split so each one (and heavy deps like charts) loads on first visit.
const page = <K extends string>(load: () => Promise<Record<K, ComponentType>>, name: K) =>
  lazy(() => load().then((module) => ({ default: module[name] })));

const AssistantPage = page(() => import('@/features/assistant/AssistantPage'), 'AssistantPage');
const MyAttendancePage = page(() => import('@/features/attendance/AttendancePages'), 'MyAttendancePage');
const TeamAttendancePage = page(() => import('@/features/attendance/AttendancePages'), 'TeamAttendancePage');
const AuditPage = page(() => import('@/features/audit/AuditPage'), 'AuditPage');
const DashboardPage = page(() => import('@/features/dashboard/DashboardPage'), 'DashboardPage');
const EmployeesPage = page(() => import('@/features/employees/EmployeesPage'), 'EmployeesPage');
const ApprovalsPage = page(() => import('@/features/leave/ApprovalsPage'), 'ApprovalsPage');
const LeavePage = page(() => import('@/features/leave/LeavePage'), 'LeavePage');
const PayrollPage = page(() => import('@/features/payroll/PayrollPage'), 'PayrollPage');
const PayslipsPage = page(() => import('@/features/payroll/PayslipsPage'), 'PayslipsPage');
const SettingsPage = page(() => import('@/features/settings/SettingsPage'), 'SettingsPage');

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      // Client errors (401/403/404/422…) will not succeed on retry.
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status >= 400 && error.status < 500) && failureCount < 2,
    },
  },
});

const STAFF: Role[] = ['hr', 'employee'];
const MANAGERS: Role[] = ['admin', 'hr'];

function only(roles: Role[], page: ReactNode) {
  return <RequireRole roles={roles}>{page}</RequireRole>;
}

function NotFoundPage() {
  return (
    <EmptyState
      icon={Compass}
      title="Page not found"
      description="The page you are looking for does not exist."
      action={
        <Link to="/" className="text-sm font-medium text-brand-700 hover:text-brand-800">
          Back to dashboard
        </Link>
      }
      className="py-24"
    />
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <AuthProvider>
          <BrowserRouter>
            <Routes>
              <Route path="/setup" element={<SetupPage />} />
              <Route
                path="/login"
                element={
                  <RequireSetup>
                    <GuestOnly>
                      <LoginPage />
                    </GuestOnly>
                  </RequireSetup>
                }
              />
              <Route
                element={
                  <RequireSetup>
                    <RequireAuth>
                      <AppLayout />
                    </RequireAuth>
                  </RequireSetup>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="assistant" element={<AssistantPage />} />
                <Route path="attendance" element={only(STAFF, <MyAttendancePage />)} />
                <Route path="leave" element={only(STAFF, <LeavePage />)} />
                <Route path="payslips" element={only(STAFF, <PayslipsPage />)} />
                <Route path="employees" element={only(MANAGERS, <EmployeesPage />)} />
                <Route path="team-attendance" element={only(MANAGERS, <TeamAttendancePage />)} />
                <Route path="approvals" element={only(MANAGERS, <ApprovalsPage />)} />
                <Route path="payroll" element={only(MANAGERS, <PayrollPage />)} />
                <Route path="settings" element={only(['admin'], <SettingsPage />)} />
                <Route path="audit" element={only(['admin'], <AuditPage />)} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>
            </Routes>
          </BrowserRouter>
        </AuthProvider>
      </ToastProvider>
    </QueryClientProvider>
  );
}
