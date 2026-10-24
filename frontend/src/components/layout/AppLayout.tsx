import { KeyRound, LogOut, Menu, X } from 'lucide-react';
import { Suspense, useState } from 'react';
import { NavLink, Outlet } from 'react-router-dom';

import { useSetupStatus } from '@/api/auth';
import { Avatar } from '@/components/ui/display';
import { PageLoader } from '@/components/ui/feedback';
import { ChangePasswordModal } from '@/features/auth/ChangePasswordModal';
import { useAuth, useCurrentUser } from '@/features/auth/auth-context';
import { cn } from '@/lib/cn';
import { ROLE_LABELS } from '@/lib/roles';
import { navigationFor } from './navigation';

export function Logo({ companyName }: { companyName?: string | null }) {
  return (
    <div className="flex items-center gap-3">
      <span className="grid size-9 place-items-center rounded-lg bg-brand-600 text-sm font-bold text-white shadow-sm">
        H
      </span>
      <div className="leading-tight">
        <p className="text-sm font-semibold text-slate-900">HCM Lite</p>
        {companyName && <p className="max-w-36 truncate text-xs text-slate-500">{companyName}</p>}
      </div>
    </div>
  );
}

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const user = useCurrentUser();
  const { signOut } = useAuth();
  const { data: setup } = useSetupStatus();
  const [passwordOpen, setPasswordOpen] = useState(false);

  return (
    <div className="flex h-full flex-col bg-white">
      <div className="flex h-16 items-center border-b border-slate-100 px-5">
        <Logo companyName={setup?.company_name} />
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-5">
        {navigationFor(user.role).map((section) => (
          <div key={section.title}>
            <p className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">{section.title}</p>
            <ul className="space-y-0.5">
              {section.items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.to === '/'}
                    onClick={onNavigate}
                    className={({ isActive }) =>
                      cn(
                        'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                        isActive ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
                      )
                    }
                  >
                    <item.icon className="size-[18px]" />
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>

      <div className="border-t border-slate-100 p-3">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2">
          <Avatar name={user.employee.full_name} size="sm" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-slate-900">{user.employee.full_name}</p>
            <p className="truncate text-xs text-slate-500">
              {ROLE_LABELS[user.role]} · {user.email}
            </p>
          </div>
        </div>
        <div className="mt-1 grid grid-cols-2 gap-1">
          <button
            type="button"
            onClick={() => setPasswordOpen(true)}
            className="flex items-center justify-center gap-2 rounded-lg px-2 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50"
          >
            <KeyRound className="size-4" /> Password
          </button>
          <button
            type="button"
            onClick={signOut}
            className="flex items-center justify-center gap-2 rounded-lg px-2 py-2 text-xs font-medium text-slate-600 hover:bg-rose-50 hover:text-rose-600"
          >
            <LogOut className="size-4" /> Sign out
          </button>
        </div>
      </div>
      <ChangePasswordModal open={passwordOpen} onClose={() => setPasswordOpen(false)} />
    </div>
  );
}

export function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data: setup } = useSetupStatus();

  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-slate-200 lg:block">
        <Sidebar />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setMobileOpen(false)} aria-hidden />
          <aside className="absolute inset-y-0 left-0 w-72 shadow-xl">
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              className="absolute top-4 -right-12 rounded-lg bg-white/90 p-2 text-slate-600"
              aria-label="Close menu"
            >
              <X className="size-5" />
            </button>
            <Sidebar onNavigate={() => setMobileOpen(false)} />
          </aside>
        </div>
      )}

      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-slate-200 bg-white/90 px-4 backdrop-blur lg:hidden">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            className="rounded-lg p-2 text-slate-600 hover:bg-slate-100"
            aria-label="Open menu"
          >
            <Menu className="size-5" />
          </button>
          <Logo companyName={setup?.company_name} />
        </header>
        <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-10">
          <Suspense fallback={<PageLoader />}>
            <Outlet />
          </Suspense>
        </main>
      </div>
    </div>
  );
}
