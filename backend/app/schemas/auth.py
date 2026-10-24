from pydantic import BaseModel, EmailStr, Field

from ..models import Role
from .common import EmployeeBrief, ORMModel

PASSWORD_CONSTRAINTS = {"min_length": 8, "max_length": 72}  # bcrypt ignores bytes beyond 72


class SetupStatus(BaseModel):
    ready: bool
    company_name: str | None = None


class SetupRequest(BaseModel):
    company_name: str = Field(min_length=2, max_length=120)
    admin_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(**PASSWORD_CONSTRAINTS)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(**PASSWORD_CONSTRAINTS)


class UserOut(ORMModel):
    id: int
    email: str
    role: Role
    employee: EmployeeBrief


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut
