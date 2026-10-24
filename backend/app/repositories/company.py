from datetime import date

from supabase import Client

from ..db.query import Row, execute, first, payload
from ..models import Company, Holiday


def find(db: Client) -> Company | None:
    row = first(db.table("companies").select("*").order("id"))
    return Company.model_validate(row) if row else None


def create(db: Client, values: Row) -> Company:
    (row,) = execute(db.table("companies").insert(payload(values)))
    return Company.model_validate(row)


def update(db: Client, company_id: int, changes: Row) -> Company:
    (row,) = execute(db.table("companies").update(payload(changes)).eq("id", company_id))
    return Company.model_validate(row)


def delete(db: Client, company_id: int) -> None:
    execute(db.table("companies").delete().eq("id", company_id))


def list_holidays(db: Client) -> list[Holiday]:
    return [Holiday.model_validate(row) for row in execute(db.table("holidays").select("*").order("day"))]


def holiday_days_between(db: Client, start: date, end: date) -> set[date]:
    rows = execute(db.table("holidays").select("day").gte("day", start.isoformat()).lte("day", end.isoformat()))
    return {date.fromisoformat(row["day"]) for row in rows}


def get_holiday(db: Client, holiday_id: int) -> Holiday | None:
    row = first(db.table("holidays").select("*").eq("id", holiday_id))
    return Holiday.model_validate(row) if row else None


def create_holiday(db: Client, name: str, day: date) -> Holiday:
    query = db.table("holidays").insert(payload({"name": name, "day": day}))
    (row,) = execute(query, conflict="A holiday already exists on that date")
    return Holiday.model_validate(row)


def delete_holiday(db: Client, holiday_id: int) -> None:
    execute(db.table("holidays").delete().eq("id", holiday_id))
