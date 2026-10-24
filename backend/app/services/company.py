from datetime import date, time

from supabase import Client

from ..core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from ..core.security import hash_password
from ..models import Company, Holiday, Role, User
from ..repositories import company as company_repo
from ..repositories import people as people_repo
from ..schemas.auth import SetupRequest
from ..schemas.company import CompanyUpdate, HolidayCreate
from . import audit

DEFAULT_POLICY = {
    "timezone": "Asia/Karachi",
    "office_start": time(9, 0),
    "grace_minutes": 15,
    "weekend_days": "saturday,sunday",
}


def find_company(db: Client) -> Company | None:
    return company_repo.find(db)


def get_company(db: Client) -> Company:
    company = company_repo.find(db)
    if company is None:
        raise BusinessRuleError("Complete first-run company setup first")
    return company


def setup_company(db: Client, data: SetupRequest) -> User:
    """Create the company and its first Admin. Only allowed once.

    PostgREST has no multi-statement transactions, so earlier inserts are rolled back by hand
    if a later one fails.
    """
    if company_repo.find(db):
        raise ConflictError("Company has already been configured")

    email = data.email.lower()
    company = company_repo.create(db, {"name": data.company_name, **DEFAULT_POLICY})
    try:
        profile = people_repo.create_employee(
            db,
            {
                "full_name": data.admin_name,
                "email": email,
                "designation": "Administrator",
                "join_date": date.today(),
                "monthly_salary": 0,
                "is_active": True,
            },
        )
        try:
            admin = people_repo.create_user(
                db, email=email, password_hash=hash_password(data.password), role=Role.ADMIN, employee_id=profile.id
            )
        except Exception:
            people_repo.delete_employee(db, profile.id)
            raise
    except Exception:
        company_repo.delete(db, company.id)
        raise

    audit.record(db, admin, "company.setup", company.name)
    return admin


def update_company(db: Client, actor: User, data: CompanyUpdate) -> Company:
    company = get_company(db)
    changes = data.model_dump(exclude_unset=True)
    if "weekend_days" in changes:
        changes["weekend_days"] = ",".join(sorted(set(changes["weekend_days"])))
    updated = company_repo.update(db, company.id, changes) if changes else company
    audit.record(db, actor, "company.updated", ", ".join(changes) or "no changes")
    return updated


def list_holidays(db: Client) -> list[Holiday]:
    return company_repo.list_holidays(db)


def add_holiday(db: Client, actor: User, data: HolidayCreate) -> Holiday:
    holiday = company_repo.create_holiday(db, data.name, data.day)
    audit.record(db, actor, "holiday.created", f"{data.name} ({data.day})")
    return holiday


def delete_holiday(db: Client, actor: User, holiday_id: int) -> None:
    holiday = company_repo.get_holiday(db, holiday_id)
    if holiday is None:
        raise NotFoundError("Holiday not found")
    company_repo.delete_holiday(db, holiday_id)
    audit.record(db, actor, "holiday.deleted", f"{holiday.name} ({holiday.day})")
