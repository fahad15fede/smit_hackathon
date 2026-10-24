import {
  CalendarCheck,
  CalendarDays,
  ClipboardCheck,
  LayoutDashboard,
  type LucideIcon,
  ReceiptText,
  ScrollText,
  Settings,
  Sparkles,
  Users,
  Wallet,
} from 'lucide-react';

import type { Role } from '@/types/api';

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  roles: Role[];
}

export interface NavSection {
  title: string;
  items: NavItem[];
}

const EVERYONE: Role[] = ['admin', 'hr', 'employee'];
const STAFF: Role[] = ['hr', 'employee'];
const MANAGERS: Role[] = ['admin', 'hr'];

export const NAV_SECTIONS: NavSection[] = [
  {
    title: 'Overview',
    items: [
      { to: '/', label: 'Dashboard', icon: LayoutDashboard, roles: EVERYONE },
      { to: '/assistant', label: 'Assistant', icon: Sparkles, roles: EVERYONE },
    ],
  },
  {
    title: 'My work',
    items: [
      { to: '/attendance', label: 'Attendance', icon: CalendarCheck, roles: STAFF },
      { to: '/leave', label: 'Leave', icon: CalendarDays, roles: STAFF },
      { to: '/payslips', label: 'Payslips', icon: ReceiptText, roles: STAFF },
    ],
  },
  {
    title: 'Manage',
    items: [
      { to: '/employees', label: 'Employees', icon: Users, roles: MANAGERS },
      { to: '/team-attendance', label: 'Team attendance', icon: CalendarCheck, roles: MANAGERS },
      { to: '/approvals', label: 'Leave approvals', icon: ClipboardCheck, roles: MANAGERS },
      { to: '/payroll', label: 'Payroll', icon: Wallet, roles: MANAGERS },
    ],
  },
  {
    title: 'Administration',
    items: [
      { to: '/settings', label: 'Settings', icon: Settings, roles: ['admin'] },
      { to: '/audit', label: 'Audit log', icon: ScrollText, roles: ['admin'] },
    ],
  },
];

export function navigationFor(role: Role): NavSection[] {
  return NAV_SECTIONS.map((section) => ({
    ...section,
    items: section.items.filter((item) => item.roles.includes(role)),
  })).filter((section) => section.items.length > 0);
}
