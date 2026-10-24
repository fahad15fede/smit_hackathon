from fastapi import APIRouter, status

from ...core.security import create_access_token
from ...models import User
from ...schemas.auth import LoginRequest, PasswordChangeRequest, SetupRequest, SetupStatus, TokenOut, UserOut
from ...services import auth as auth_service
from ...services import company as company_service
from ..deps import CurrentUser, Db

router = APIRouter(tags=["auth"])


def _token_for(user: User) -> TokenOut:
    return TokenOut(access_token=create_access_token(user.id, user.role), user=UserOut.model_validate(user))


@router.get("/setup/status", response_model=SetupStatus)
def setup_status(db: Db):
    company = company_service.find_company(db)
    return SetupStatus(ready=company is not None, company_name=company.name if company else None)


@router.post("/setup", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def setup(payload: SetupRequest, db: Db):
    return _token_for(company_service.setup_company(db, payload))


@router.post("/auth/login", response_model=TokenOut)
def login(payload: LoginRequest, db: Db):
    return _token_for(auth_service.authenticate(db, payload.email, payload.password))


@router.get("/auth/me", response_model=UserOut)
def me(user: CurrentUser):
    return user


@router.post("/auth/password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: PasswordChangeRequest, db: Db, user: CurrentUser):
    auth_service.change_password(db, user, payload.current_password, payload.new_password)
