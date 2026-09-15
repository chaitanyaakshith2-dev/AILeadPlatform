HEAD

# LeadFlow AI

LeadFlow AI is an AI-powered lead management SaaS for small businesses. It will eventually capture customer inquiries, analyze them, score and extract lead information, store leads, and help businesses follow up.

## Current architecture

- `frontend/`: Next.js with TypeScript and the App Router.
- `backend/`: Python FastAPI service with Supabase token validation and authenticated lead CRUD endpoints.
- `docs/`: Project documentation space.

The frontend and backend are separate services so they can evolve independently. The frontend will provide the user experience, while the backend will own API behavior and future lead-processing logic.

## Prerequisites

- Node.js 20 or newer and npm
- Python 3.11 or newer

## Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000.

## Start the backend

Create and activate a virtual environment from the repository root:

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

macOS/Linux:

```bash
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at http://localhost:8000.

## Verify the health endpoint

With the backend running:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{ "status": "ok" }
```

Interactive API documentation is available at http://localhost:8000/docs.

## Environment configuration

Copy the relevant `.env.example` file to `.env` for local configuration when needed. Never add real API keys or secrets to the repository.

For the frontend, configure `frontend/.env` with the public Supabase project values and the backend URL:

```env
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

For the backend, configure `backend/.env` with the same project URL and public anon key:

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
PUBLIC_API_BASE_URL=http://localhost:8000
AI_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
# Or use Gemini instead:
# AI_PROVIDER=gemini
# GEMINI_API_KEY=
# GEMINI_MODEL=gemini-2.0-flash
```

`SUPABASE_SERVICE_ROLE_KEY` is server-only and is used only by the tokenized public lead webhook. It must never be exposed to the frontend or committed.

## Database setup

Run these files in order in the Supabase SQL Editor if they have not already been applied:

1. [docs/database.sql](docs/database.sql)
2. [docs/auth-migration.sql](docs/auth-migration.sql)
3. [docs/ai-migration.sql](docs/ai-migration.sql)
4. [docs/settings-migration.sql](docs/settings-migration.sql)

The authentication migration requires the `leads` table to be empty because it adds the required `user_id` column. Each lead is owned by the authenticated Supabase user who created it. The AI migration adds nullable JSONB analysis data. The settings migration adds tenant settings, a generated webhook token, and RLS policies.

The public capture endpoint is available at the webhook URL shown in the dashboard settings page. Send a JSON `POST` containing `name`, `email`, `company`, and `message`. The URL token determines the target tenant; no `user_id` is accepted from the public request.

## Current project status

Authentication, tenant ownership, and opt-in AI lead analysis are implemented. Users can sign up, log in, log out, manage their own leads, and request structured scoring and analysis through the protected dashboard and authenticated API. Payments, email automation, n8n workflows, and production deployment are intentionally not implemented yet.

# AILeadPlatform

a0505c3ae04481f814eda439d8e85f05e644e028
