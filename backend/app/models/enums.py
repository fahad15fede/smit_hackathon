from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    HR = "hr"
    EMPLOYEE = "employee"


class AttendanceStatus(StrEnum):
    PRESENT = "present"
    LATE = "late"


class LeaveStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class PayrollStatus(StrEnum):
    DRAFT = "draft"
    FINALIZED = "finalized"
