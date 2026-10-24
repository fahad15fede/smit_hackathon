"""Domain errors raised by services and translated to HTTP responses in one place."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class AuthenticationError(AppError):
    status_code = 401


class PermissionDeniedError(AppError):
    status_code = 403


class NotFoundError(AppError):
    status_code = 404


class ConflictError(AppError):
    status_code = 409


class BusinessRuleError(AppError):
    status_code = 422


class DatabaseUnavailableError(AppError):
    """Supabase could not be reached or is misconfigured (bad key, missing tables)."""

    status_code = 503


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
