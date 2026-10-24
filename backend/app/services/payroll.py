from calendar import monthrange
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from supabase import Client

from ..core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from ..models import PayrollRun, PayrollStatus, Payslip, User
from ..repositories import attendance as attendance_repo
from ..repositories import leaves as leave_repo
from ..repositories import payroll as payroll_repo
from ..repositories import people as people_repo
from . import audit
from .calendar import WorkCalendar, company_today, iter_days
from .company import get_company

CENT = Decimal("0.01")


def list_runs(db: Client) -> list[PayrollRun]:
    return payroll_repo.list_runs(db)


def get_run(db: Client, run_id: int) -> PayrollRun:
    run = payroll_repo.get_run(db, run_id)
    if run is None:
        raise NotFoundError("Payroll run not found")
    return run


def _month_bounds(month: str) -> tuple[date, date]:
    year, mon = map(int, month.split("-"))
    return date(year, mon, 1), date(year, mon, monthrange(year, mon)[1])


def create_run(db: Client, actor: User, month: str) -> PayrollRun:
    """Draft a payroll run.

    Salary is paid per working day of the month. A working day is unpaid when it falls before
    the employee's join date, is covered by approved unpaid leave, or (up to today) has neither
    an attendance record nor approved paid leave.
    """
    if payroll_repo.month_exists(db, month):
        raise ConflictError(f"Payroll for {month} already exists")

    company = get_company(db)
    first, last = _month_bounds(month)
    today = company_today(company)
    if first > today:
        raise BusinessRuleError("Payroll cannot be run for a future month")

    working_days = WorkCalendar(db, company, first, last).working_days(first, last)
    counted_until = min(last, today)

    attended: dict[int, set[date]] = defaultdict(set)
    for row in attendance_repo.days_between(db, first, last):
        attended[row["employee_id"]].add(row["day"])

    paid_leave: dict[int, set[date]] = defaultdict(set)
    unpaid_leave: dict[int, set[date]] = defaultdict(set)
    for leave in leave_repo.approved_overlapping(db, first, last):
        target = paid_leave if leave.leave_type.is_paid else unpaid_leave
        target[leave.employee_id].update(iter_days(max(leave.start_date, first), min(leave.end_date, last)))

    payslips = []
    for employee in people_repo.list_payable(db, joined_by=last):
        unpaid = sum(
            1
            for day in working_days
            if day < employee.join_date
            or day in unpaid_leave[employee.id]
            or (
                day <= counted_until
                and day not in attended[employee.id]
                and day not in paid_leave[employee.id]
            )
        )
        gross = employee.monthly_salary
        daily_rate = gross / len(working_days) if working_days else Decimal("0")
        deduction = min(gross, (daily_rate * unpaid).quantize(CENT, rounding=ROUND_HALF_UP))
        payslips.append(
            {
                "employee_id": employee.id,
                "working_days": len(working_days),
                "unpaid_days": unpaid,
                "gross": gross,
                "deduction": deduction,
                "net": gross - deduction,
            }
        )

    run = payroll_repo.create_run(db, month, actor.id, payslips)
    audit.record(db, actor, "payroll.drafted", f"{month}: {len(payslips)} payslip(s)")
    return run


def _get_draft(db: Client, run_id: int) -> PayrollRun:
    run = get_run(db, run_id)
    if run.status is PayrollStatus.FINALIZED:
        raise ConflictError("This payroll run is already finalized")
    return run


def finalize_run(db: Client, actor: User, run_id: int) -> PayrollRun:
    run = _get_draft(db, run_id)
    finalized = payroll_repo.update_run(
        db, run_id, {"status": PayrollStatus.FINALIZED, "finalized_at": datetime.now(timezone.utc)}
    )
    audit.record(db, actor, "payroll.finalized", run.month)
    return finalized


def delete_draft(db: Client, actor: User, run_id: int) -> None:
    run = _get_draft(db, run_id)
    payroll_repo.delete_run(db, run_id)
    audit.record(db, actor, "payroll.draft_deleted", run.month)


def payslips_for(db: Client, employee_id: int) -> list[Payslip]:
    """Payslips an employee may see: only those from finalized runs."""
    return payroll_repo.finalized_payslips_for(db, employee_id)
