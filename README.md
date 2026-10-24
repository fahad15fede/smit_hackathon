# HCM Lite

A lightweight human-capital management app: employees, attendance, leave, payroll and an HR assistant,
with Admin / HR / Employee roles and a full audit trail.

- **Backend:** FastAPI with **Supabase** (Postgres through the Supabase Python client / Data API)
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS v4, TanStack Query, React Hook Form, Recharts

## Project structure

```
backend/
  app/
    core/          config (env settings), security (JWT/bcrypt), domain errors
    db/            Supabase client and query execution (maps DB errors to API errors)
    models/        typed records mirroring the Supabase tables, plus enums
    repositories/  every Supabase query lives here, one module per domain
    schemas/       Pydantic request/response models (the API contract)
    services/      business rules: no HTTP or query-building code, raise domain errors
    api/
      deps.py      Supabase client, current user, role guards
      routes/      thin HTTP handlers that validate input, call a service and return a schema
    main.py        app factory
  tests/           end-to-end API tests against an in-memory Supabase fake
supabase/
  schema.sql       tables, constraints and Row Level Security; run once in the SQL Editor
frontend/src/
  api/             typed endpoint calls and React Query hooks, one file per domain
  components/      ui/ (design-system primitives) and layout/ (app shell, navigation)
  features/        one folder per feature: pages and feature-specific components
  lib/             HTTP client, formatting, helpers
  types/           TypeScript mirrors of the backend schemas
```

## Supabase setup

1. Create a project at [supabase.com](https://supabase.com).
2. **Create the tables:** open **SQL Editor → New query**, paste the contents of
   [`supabase/schema.sql`](supabase/schema.sql), and click **Run**. The script is safe to re-run.
3. Copy `backend/.env.example` to `backend/.env` and fill in:
   - `SUPABASE_URL`: **Project Settings → Data API → Project URL** (`https://<project-ref>.supabase.co`)
   - `SUPABASE_SECRET_KEY`: **Project Settings → API Keys → Secret keys** (`sb_secret_…`).
     Older projects can use the legacy `service_role` key.
   - `JWT_SECRET`: generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"`

**Why the secret key, not the publishable/anon key?** HCM Lite authenticates users in its own
backend, so the backend is the only thing that talks to Supabase. The publishable key is public
by design (it ships to browsers). The schema turns on Row Level Security and revokes table access
from the public roles, so that key cannot read salaries or any other HR data. The secret key
bypasses RLS and must stay on the server. The frontend never needs a Supabase key.

## Running locally

```bash
# Backend (from the repository root)
python -m venv .venv
./.venv/Scripts/python -m pip install -r backend/requirements.txt
cd backend
../.venv/Scripts/python -m uvicorn app.main:app --reload    # http://localhost:8000/docs

# Frontend
cd frontend
cp .env.example .env
npm install
npm run dev                                                 # http://localhost:5173
```

On first launch the app opens the **setup** screen, where you create the company and the first Admin.
The Admin then configures working hours, departments, leave types and holidays under **Settings**
and adds HR staff from **Employees**.

## Tests

```bash
cd backend
../.venv/Scripts/python -m pytest
```

The tests use an in-memory fake of the Supabase client and never read `backend/.env`, so they
do not touch your Supabase project or call Gemini.

## Roles

| Capability                                       | Admin | HR  | Employee |
| ------------------------------------------------ | :---: | :-: | :------: |
| Organization dashboard, team attendance          |   ✓   |  ✓  |          |
| Personal check-in, leave requests, payslips      |       |  ✓  |    ✓     |
| Add employees                                    |   ✓   |  ✓  |          |
| Create HR / Admin accounts                       |   ✓   |     |          |
| Approve or reject leave (never your own)         |   ✓   |  ✓  |          |
| Draft payroll                                    |       |  ✓  |          |
| Finalize payroll                                 |   ✓   |     |          |
| Company settings, audit log                      |   ✓   |     |          |
| HR assistant (answers use only data you can see) |   ✓   |  ✓  |    ✓     |

## Business rules

- **Attendance:** one check-in per working day, timed by the server in the company timezone. Check-ins
  after *office start + grace period* are marked late.
- **Leave:** only working days are counted (weekends and holidays are excluded). Requests may not overlap
  or exceed the remaining yearly balance, which counts pending requests as well as approved ones.
- **Payroll:** salary is paid per working day. A working day is unpaid if it falls before the join date,
  is covered by approved unpaid leave, or (up to today) has neither a check-in nor approved paid leave.
  Employees see a payslip only after an Admin finalizes the run.
- **Assistant:** uses Gemini when `GEMINI_API_KEY` is set and falls back to rule-based answers otherwise.
