"""Request-scoped dependencies: Supabase client, authenticated user and role guards."""

from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from supabase import Client

from ..core.exceptions import AuthenticationError, PermissionDeniedError
from ..core.security import decode_access_token
from ..db.client import get_db
from ..models import Role, User
from ..services import auth as auth_service

bearer_scheme = HTTPBearer(auto_error=False)

Db = Annotated[Client, Depends(get_db)]


def get_current_user(
    db: Db,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    user_id = decode_access_token(credentials.credentials) if credentials else None
    user = auth_service.get_active_user(db, user_id) if user_id is not None else None
    if user is None:
        raise AuthenticationError("Your session is invalid or has expired")
    return user


def require_roles(*roles: Role):
    def guard(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise PermissionDeniedError("You do not have permission to perform this action")
        return user

    return guard


CurrentUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_roles(Role.ADMIN))]
ManagerUser = Annotated[User, Depends(require_roles(Role.ADMIN, Role.HR))]
HRUser = Annotated[User, Depends(require_roles(Role.HR))]
