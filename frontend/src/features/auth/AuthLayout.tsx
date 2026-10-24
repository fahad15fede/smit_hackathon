import { CalendarCheck, ShieldCheck, Wallet } from 'lucide-react';
import type { ReactNode } from 'react';

import { Logo } from '@/components/layout/AppLayout';

const HIGHLIGHTS = [
  { icon: CalendarCheck, title: 'Attendance & leave', text: 'Server-timed check-ins and balance-aware leave requests.' },
  { icon: Wallet, title: 'Payroll in minutes', text: 'Draft, review and finalize monthly payroll with payslips.' },
  { icon: ShieldCheck, title: 'Role-based access', text: 'Admin, HR and Employee views with a full audit trail.' },
];

export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_minmax(480px,560px)]">
      <aside className="relative hidden overflow-hidden bg-slate-900 p-12 text-white lg:flex lg:flex-col lg:justify-between">
        <div className="pointer-events-none absolute -top-40 -left-40 size-[480px] rounded-full bg-brand-500/25 blur-3xl" />
        <div className="pointer-events-none absolute -right-32 -bottom-48 size-[420px] rounded-full bg-sky-500/20 blur-3xl" />
        <div className="relative flex items-center gap-3">
          <span className="grid size-10 place-items-center rounded-xl bg-brand-500 font-bold">H</span>
          <span className="text-lg font-semibold">HCM Lite</span>
        </div>
        <div className="relative max-w-md">
          <h2 className="text-4xl leading-tight font-semibold tracking-tight">
            People operations, <span className="text-brand-400">without the paperwork.</span>
          </h2>
          <ul className="mt-10 space-y-6">
            {HIGHLIGHTS.map(({ icon: Icon, title: heading, text }) => (
              <li key={heading} className="flex gap-4">
                <span className="grid size-10 shrink-0 place-items-center rounded-lg bg-white/10 ring-1 ring-white/15">
                  <Icon className="size-5 text-brand-300" />
                </span>
                <div>
                  <p className="font-medium">{heading}</p>
                  <p className="mt-0.5 text-sm text-slate-300">{text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <p className="relative text-xs text-slate-400">© {new Date().getFullYear()} HCM Lite</p>
      </aside>

      <main className="flex items-center justify-center bg-white px-6 py-12 sm:px-12">
        <div className="w-full max-w-sm">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-900">{title}</h1>
          <p className="mt-2 text-sm text-slate-500">{subtitle}</p>
          <div className="mt-8">{children}</div>
        </div>
      </main>
    </div>
  );
}
