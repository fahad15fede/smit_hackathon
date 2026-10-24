// Mirrors the backend response/request schemas in backend/app/schemas.

export type Role = 'admin' | 'hr' | 'employee';
export type AttendanceStatus = 'present' | 'late';
export type LeaveStatus = 'pending' | 'approved' | 'rejected' | 'cancelled';
export type PayrollStatus = 'draft' | 'finalized';
export type Weekday = 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday' | 'saturday' | 'sunday';

export interface EmployeeBrief {
  id: number;
  full_name: string;
  designation: string;
}

export interface User {
  id: number;
  email: string;
  role: Role;
  employee: EmployeeBrief;
}

export interface Session {
  access_token: string;
  token_type: string;
  user: User;
}

export interface SetupStatus {
  ready: boolean;
  company_name: string | null;
}

export interface Company {
  id: number;
  name: string;
  timezone: string;
  office_start: string;
  grace_minutes: number;
  weekend_days: Weekday[];
}

export interface Holiday {
  id: number;
  name: string;
  day: string;
}

export interface Department {
  id: number;
  name: string;
}

export interface Employee {
  id: number;
  full_name: string;
  email: string;
  designation: string;
  join_date: string;
  monthly_salary: number;
  phone: string | null;
  address: string | null;
  is_active: boolean;
  department: Department | null;
  role: Role;
}

export interface EmployeeInput {
  full_name: string;
  email: string;
  designation: string;
  join_date: string;
  monthly_salary: number;
  department_id: number | null;
  phone: string | null;
  role: Role;
  password: string;
}

export type EmployeeUpdate = Partial<
  Pick<Employee, 'full_name' | 'designation' | 'monthly_salary' | 'phone' | 'address' | 'is_active'> & {
    department_id: number | null;
  }
>;

export interface AttendanceRecord {
  id: number;
  day: string;
  check_in: string;
  check_out: string | null;
  status: AttendanceStatus;
  employee: EmployeeBrief;
}

export interface LeaveType {
  id: number;
  name: string;
  annual_quota: number;
  is_paid: boolean;
}

export interface LeaveRequest {
  id: number;
  start_date: string;
  end_date: string;
  working_days: number;
  reason: string;
  status: LeaveStatus;
  review_comment: string | null;
  reviewed_at: string | null;
  created_at: string;
  employee: EmployeeBrief;
  leave_type: LeaveType;
}

export interface LeaveInput {
  leave_type_id: number;
  start_date: string;
  end_date: string;
  reason: string;
}

export interface LeaveBalance {
  leave_type: LeaveType;
  year: number;
  used: number;
  pending: number;
  remaining: number;
}

export interface PayrollRun {
  id: number;
  month: string;
  status: PayrollStatus;
  created_at: string;
  finalized_at: string | null;
  employee_count: number;
  total_gross: number;
  total_deduction: number;
  total_net: number;
}

export interface Payslip {
  id: number;
  month: string;
  status: PayrollStatus;
  working_days: number;
  unpaid_days: number;
  gross: number;
  deduction: number;
  net: number;
  employee: EmployeeBrief;
}

export interface PayrollRunDetail extends PayrollRun {
  payslips: Payslip[];
}

export interface TrendPoint {
  day: string;
  present: number;
  late: number;
}

export interface OrganizationDashboard {
  today: string;
  is_working_day: boolean;
  headcount: number;
  present: number;
  late: number;
  on_leave: number;
  absent: number;
  pending_leaves: number;
  month_attendance_rate: number | null;
  trend: TrendPoint[];
  recent_pending: LeaveRequest[];
}

export interface PersonalDashboard {
  today: string;
  is_working_day: boolean;
  attendance: AttendanceRecord | null;
  balances: LeaveBalance[];
  pending_leaves: number;
  latest_payslip: Payslip | null;
}

export interface AuditEntry {
  id: number;
  action: string;
  detail: string;
  created_at: string;
  actor: { id: number; email: string } | null;
}

export interface ChatTurn {
  role: 'user' | 'assistant';
  text: string;
}

export interface ChatResponse {
  answer: string;
  ai_generated: boolean;
  /** "quick_reply" answers (greetings, help, navigation) never reach the AI model. */
  source: 'ai' | 'quick_reply' | 'fallback';
  tools_used: string[];
}

export interface DashboardSummary {
  bullets: string[];
  ai_generated: boolean;
  message: string | null;
}

export interface LeaveDraft {
  leave_type_id: number;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  reason: string;
}

export interface LeaveDraftResponse {
  draft: LeaveDraft | null;
  ai_generated: boolean;
  message: string | null;
}
