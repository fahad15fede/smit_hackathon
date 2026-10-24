from supabase import Client

from ..core.exceptions import AuthenticationError, BusinessRuleError
from ..core.security import hash_password, verify_password
from ..models import User
from ..repositories import people as people_repo
from . import audit


def authenticate(db: Client, email: str, password: str) -> User:
    user = people_repo.find_user_by_email(db, email.lower())
    if user is None or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    if not user.is_active:
        raise AuthenticationError("This account has been deactivated")
    return user


def get_active_user(db: Client, user_id: int) -> User | None:
    user = people_repo.get_user(db, user_id)
    return user if user and user.is_active else None


def change_password(db: Client, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise BusinessRuleError("Current password is incorrect")
    people_repo.update_user(db, user.id, {"password_hash": hash_password(new_password)})
    audit.record(db, user, "password.changed", user.email)
