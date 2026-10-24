from supabase import Client

from ..db.query import Row, execute, first, payload
from ..models import PayrollRun, PayrollStatus, Payslip

EMPLOYEE_REF = "employee:employees!employee_id(id,full_name,designation)"
RUN_SELECT = f"*, payslips!payroll_run_id(*, {EMPLOYEE_REF})"
PAYSLIP_SELECT = f"*, {EMPLOYEE_REF}, payroll_run:payroll_runs!payroll_run_id(month,status)"


def _to_run(row: Row) -> PayrollRun:
    ref = {"month": row["month"], "status": row["status"]}
    slips = sorted(row.get("payslips") or [], key=lambda slip: slip["id"])
    return PayrollRun.model_validate({**row, "payslips": [{**slip, "payroll_run": ref} for slip in slips]})


def list_runs(db: Client) -> list[PayrollRun]:
    return [_to_run(row) for row in execute(db.table("payroll_runs").select(RUN_SELECT).order("month", desc=True))]


def get_run(db: Client, run_id: int) -> PayrollRun | None:
    row = first(db.table("payroll_runs").select(RUN_SELECT).eq("id", run_id))
    return _to_run(row) if row else None


def month_exists(db: Client, month: str) -> bool:
    return first(db.table("payroll_runs").select("id").eq("month", month)) is not None


def create_run(db: Client, month: str, created_by_id: int, payslips: list[Row]) -> PayrollRun:
    """Insert a draft run with its payslips. Removes the run again if the payslips fail to save."""
    values = payload({"month": month, "status": PayrollStatus.DRAFT, "created_by_id": created_by_id})
    (run,) = execute(db.table("payroll_runs").insert(values), conflict=f"Payroll for {month} already exists")
    try:
        if payslips:
            execute(db.table("payslips").insert(payload([{**slip, "payroll_run_id": run["id"]} for slip in payslips])))
    except Exception:
        delete_run(db, run["id"])
        raise
    return get_run(db, run["id"])


def update_run(db: Client, run_id: int, changes: Row) -> PayrollRun:
    execute(db.table("payroll_runs").update(payload(changes)).eq("id", run_id))
    return get_run(db, run_id)


def delete_run(db: Client, run_id: int) -> None:
    execute(db.table("payroll_runs").delete().eq("id", run_id))  # payslips cascade


def finalized_payslips_for(db: Client, employee_id: int) -> list[Payslip]:
    finalized = execute(db.table("payroll_runs").select("id").eq("status", PayrollStatus.FINALIZED.value))
    run_ids = [row["id"] for row in finalized]
    if not run_ids:
        return []
    query = db.table("payslips").select(PAYSLIP_SELECT).eq("employee_id", employee_id).in_("payroll_run_id", run_ids)
    slips = [Payslip.model_validate(row) for row in execute(query)]
    return sorted(slips, key=lambda slip: slip.month, reverse=True)
