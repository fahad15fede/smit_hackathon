"""Company-local time and working-day calculations."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from supabase import Client

from ..models import Company
from ..repositories import company as company_repo


def company_now(company: Company) -> datetime:
    return datetime.now(ZoneInfo(company.timezone))


def company_today(company: Company) -> date:
    return company_now(company).date()


def iter_days(start: date, end: date):
    for offset in range((end - start).days + 1):
        yield start + timedelta(days=offset)


class WorkCalendar:
    """Answers "is this a working day?" using the company weekend and holiday list."""

    def __init__(self, db: Client, company: Company, start: date, end: date):
        self._weekend = company.weekend
        self._holidays = company_repo.holiday_days_between(db, start, end)

    def is_working_day(self, day: date) -> bool:
        return day not in self._holidays and day.strftime("%A").lower() not in self._weekend

    def working_days(self, start: date, end: date) -> list[date]:
        return [day for day in iter_days(start, end) if self.is_working_day(day)]
