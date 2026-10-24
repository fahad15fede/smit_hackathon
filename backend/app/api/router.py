from fastapi import APIRouter

from .routes import ai, attendance, auth, company, employees, insights, leaves, payroll

api_router = APIRouter(prefix="/api")
for module in (auth, company, employees, attendance, leaves, payroll, insights, ai):
    api_router.include_router(module.router)
