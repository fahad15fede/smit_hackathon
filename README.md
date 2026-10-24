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
do not touch your Supabase project or call the AI provider.

## Deploy (Render + Vercel)

Both services build from this GitHub repository and redeploy on every push to `main`.

**1. Backend on Render** (uses [`render.yaml`](render.yaml))
1. [dashboard.render.com](https://dashboard.render.com) → **New → Blueprint** → pick this repository.
2. Fill in the secrets it asks for: `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `GROQ_API_KEY`, and
   `FRONTEND_ORIGIN` (enter a placeholder for now; set it after step 2). `JWT_SECRET` is generated for you.
3. Wait for the deploy, then open `https://<service>.onrender.com/health`; it should return `{"status":"ok"}`.

**2. Frontend on Vercel** (uses [`frontend/vercel.json`](frontend/vercel.json))
1. [vercel.com/new](https://vercel.com/new) → import this repository → set **Root Directory** to `frontend`.
2. Add the environment variable `VITE_API_URL` = `https://<service>.onrender.com/api`, then **Deploy**.

**3. Connect them:** in Render, set `FRONTEND_ORIGIN` to your Vercel URL (for example
`https://hcm-lite.vercel.app`, no trailing slash; comma-separate several) and save. Render redeploys.

Notes: Render's free plan sleeps after 15 minutes without traffic, so the first request afterwards takes
about 30–60 seconds; open the site a minute before a demo. `VITE_API_URL` is built into the frontend, so
redeploy on Vercel after changing it.

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

## AI assistant

The assistant uses [Groq](https://console.groq.com) (OpenAI-compatible API). Set `GROQ_API_KEY` in
`backend/.env`; `GROQ_MODEL` defaults to `openai/gpt-oss-120b`. The key lives only on the backend and the
browser never calls the AI provider.

| Feature | Who | Endpoint |
| --- | --- | --- |
| Chat with tool calling | All roles | `POST /api/ai/chat` |
| Dashboard "Summarize" (3–5 bullets from the KPI numbers only) | Admin, HR | `POST /api/ai/summary` |
| Smart leave: free text to a pre-filled form the user confirms | Employee, HR | `POST /api/ai/leave-draft` |

### How a chat question is answered

1. **Quick replies first.** Greetings, thanks, goodbyes, "help / what can you do" and "how do I…" navigation
   questions are answered locally (`app/ai/quick_replies.py`). They never reach the model, use no tokens and
   don't count toward the hourly limit. A message counts as small talk only if that is all it contains, so
   "Hi, how many employees do we have?" still goes to the model.
2. **Tool round(s).** The model gets the system prompt, up to 10 previous messages and the tool list, and
   picks tools. The backend runs them with the user's own permissions and sends back the results.
   At most 4 tool rounds per question.
3. **Answer.** The model writes the reply from the tool results only. Answers are labelled "AI-generated".

- **Tools:** `get_headcount` (every department, including empty ones, plus people without a department),
  `get_attendance_summary`, `get_late_comers`, `get_leave_summary`, `get_my_leave_balance`,
  `get_payroll_summary`, `search_employees`. They call the same services as the REST API, apply the same role
  checks and are read-only. The model never touches the database.
- **System prompt** (`app/ai/prompts.py`): role, context (today, user, role, department list for Admin/HR),
  answering rules (tools for every number, period defaults, no data changes), permissions, a style guide
  (answer first, plain English, no markdown) and the company policy built from live settings. Policy questions
  are answered only from that policy; otherwise the model says it does not know.

### Tokens and limits

Measured on `openai/gpt-oss-120b` with `reasoning_effort=low`:

| Request | Prompt tokens | Completion tokens | Total |
| --- | --- | --- | --- |
| Chat question with one tool (2 model calls) | ~1,400 + ~1,500 | ~40 + ~40 | **~3,000** |
| Chat follow-up with history | grows by roughly 50–300 per previous message | | 3,000–6,000 |
| Dashboard summary | ~260 | ~250 | **~500** |
| Smart leave draft | ~250 | ~125 | **~375** |
| Quick reply (greeting, help, navigation) | 0 | 0 | **0** |

Most of a chat question's prompt is fixed: the system prompt with policy (~800 tokens) and the 7 tool
definitions (~600 tokens) are sent on every model call. JSON features retry once on invalid output, which can
double their cost.

| Limit | Value | Where it is set |
| --- | --- | --- |
| Model context window | 131,072 tokens | Groq (`openai/gpt-oss-120b`) |
| Model maximum output | 65,536 tokens | Groq |
| Output cap per model reply (reasoning + answer) | 1,500 tokens | `ai_max_output_tokens` in `config.py` |
| Reasoning effort (gpt-oss models only) | `low` | `ai_reasoning_effort` |
| Time limit per question, all rounds | 15 s | `ai_timeout_seconds` |
| Assistant requests per user | 20 per hour | `ai_requests_per_hour` (quick replies not counted) |
| Question length / history | 500 characters / last 10 messages | `schemas/ai.py` |
| **Groq account: tokens per minute** | **8,000** (free tier, measured) | your Groq plan |
| **Groq account: requests per day** | **1,000** (free tier, measured) | your Groq plan |

**What this means:** the Groq account limit is shared by all users. With 8,000 tokens per minute, about
2–3 chat questions per minute fit across the whole app. When Groq is at its limit it returns HTTP 429, and the
assistant answers "handling a lot of requests, try again in about a minute". For a demo with several people,
use a paid Groq tier or a smaller model. Your current limits are in the `x-ratelimit-*` response headers and at
[console.groq.com/settings/limits](https://console.groq.com/settings/limits); free-tier values change over time.

**Reasoning models:** gpt-oss models "think" before answering, and that hidden reasoning counts toward the
output cap. With a low cap or high effort they can run out before writing the answer (empty reply). That is why
`reasoning_effort` defaults to `low` and the cap is 1,500. It is only sent to gpt-oss models; other models
reject it.

### Usage log

Every model call is recorded in the `ai_logs` table: user, feature (`chat`, `summary`, `leave_draft`),
prompt, tools called, status (`ok`, `fallback`, `rate_limited`), latency and `prompt_tokens` /
`completion_tokens` (summed over all rounds and retries). Daily usage, for example:

```sql
select date(created_at) as day, feature, count(*) as calls,
       sum(prompt_tokens + completion_tokens) as tokens
from ai_logs group by 1, 2 order by 1 desc;
```

### Guardrails

- The API key is a backend environment variable; the browser never calls Groq.
- Tools are read-only and reuse the REST API's services and permission checks.
- The AI never saves data. Smart leave only pre-fills a form; the user submits it.
- JSON output is validated against the expected shape, retried once, and otherwise falls back to the normal form.
- 15 s deadline, a friendly fallback on any failure, and a separate "busy" message when Groq is at its limit.
