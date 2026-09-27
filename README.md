# Archidev — Finance Automation & AI Decision Support

Archidev is a multi-tenant finance operations platform that gives founders and finance teams a single, trustworthy view of their business — transactions, expenses, invoices, payables/receivables, bank reconciliation, budgeting, forecasting, and an AI assistant, all backed by proper double-entry accounting under the hood.

> Every insight and forecast is generated from real thresholds in your data — never invented. Estimates are always labeled as estimates, never presented as actuals.

## Features

- **Dashboard** — Financial Health Score, profit trend (actual vs. forecast), key balances at a glance
- **Transactions** — every posted transaction automatically generates correct double-entry journal postings
- **Expenses** — submit → review → approve/reject workflow; an approved expense instantly becomes a posted transaction
- **Invoices & Receivables** — track what customers owe you, including overdue tracking
- **Payables** — record vendor bills; posts the AP journal entry immediately
- **Bank Reconciliation** — match bank activity against your books
- **Budgets** — set and track spending against plan
- **Forecasting** — linear-trend revenue/expense/profit estimates, clearly marked as projections
- **AI Insights** — automated alerts generated only when a real threshold is crossed in your data (e.g. an invoice overdue 60+ days)
- **AI Assistant** — ask plain-English questions about your finances and get answers backed by your actual data (falls back to a rule-based assistant if no LLM key is configured)
- **Role-based access control** — Admin, Finance Manager, Accountant, and Viewer roles with a central permission matrix
- **Audit Logs & Notifications** — track changes and stay informed of important events

## Tech Stack

**Backend**
- FastAPI (Python)
- SQLAlchemy + Alembic (PostgreSQL in production, SQLite for local/demo)
- JWT authentication (python-jose, passlib/bcrypt)
- pandas / numpy / scikit-learn for categorization and forecasting
- Anthropic API (optional) for LLM-backed AI Assistant responses

**Frontend**
- React 18 + React Router
- Vite
- Tailwind CSS
- Recharts

**Infrastructure**
- Docker & docker-compose for local multi-service development
- Render blueprint for backend deployment
- Vercel config for frontend (and backend, via `backend/vercel.json`) deployment

## Project Structure

```
archidev-finance/
├── backend/
│   ├── app/
│   │   ├── core/        # settings, security
│   │   ├── database/    # SQLAlchemy session/engine
│   │   ├── models/      # ORM models (accounting, invoices, expenses, users, etc.)
│   │   ├── routes/      # FastAPI routers, one per domain area
│   │   ├── schemas/     # Pydantic request/response schemas
│   │   ├── seed/        # demo data generator
│   │   ├── services/    # business logic (ledger, forecasting, insights, AI assistant, etc.)
│   │   └── main.py      # FastAPI app entrypoint
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/  # shared UI components
│   │   ├── context/     # auth context
│   │   ├── layouts/     # app shell/layout
│   │   ├── pages/       # one page per feature area
│   │   └── services/    # API client
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── render.yaml
```

## Getting Started

### Option 1: Docker Compose (recommended)

This spins up PostgreSQL, the backend, and the frontend together.

```bash
git clone https://github.com/nabehagillani/archidev-finance.git
cd archidev-finance
cp .env.example .env   # fill in POSTGRES_PASSWORD / JWT_SECRET_KEY
docker-compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API health check: http://localhost:8000/api/health

### Option 2: Run locally without Docker

**Backend**

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Uses SQLite by default — no database setup required
uvicorn app.main:app --reload
```

Seed demo data (creates a fictional company, "Archidev", with several months of transactions, expenses, invoices, and a bank statement for reconciliation testing):

```bash
python -m app.seed.seed_data
```

Demo login (after seeding): `admin@archidev.com` / `demo1234`

**Frontend**

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on http://localhost:5173 by default and expects the backend at http://localhost:8000 (see `frontend/src/services/api.js`).

## Environment Variables

| Variable | Where | Description | Default |
|---|---|---|---|
| `DATABASE_URL` | backend | PostgreSQL connection string in production; falls back to local SQLite | `sqlite:///./finance.db` |
| `JWT_SECRET_KEY` | backend | Secret used to sign JWTs — **must be changed in production** | `CHANGE_ME_IN_PRODUCTION` |
| `CORS_ORIGINS` | backend | Comma-separated list of allowed frontend origins | `http://localhost:5173,http://localhost:3000` |
| `ANTHROPIC_API_KEY` | backend | Optional — enables real LLM-backed AI Assistant responses | unset (rule-based fallback) |
| `POSTGRES_PASSWORD` | docker-compose | Postgres password for the local `postgres` service | `change_me_in_production` |
| `UPLOAD_DIR` | backend | Where receipt uploads are stored | `./uploads` (`/tmp/uploads` on Vercel) |

See `.env.example` for the docker-compose template.

> **Note on Vercel deployments:** Vercel's serverless filesystem only allows writes to `/tmp`, and that storage doesn't persist between invocations. Receipt uploads work per-request there but won't survive a cold start — point `UPLOAD_DIR` at a mounted volume or object storage for real persistence in production.

## Running Tests

```bash
cd backend
pytest
```

Covers the ledger/double-entry logic, expense approval workflow, AI assistant, RBAC permissions, and transaction categorization.

## Deployment

- **Backend:** deploy via the included `render.yaml` Blueprint on Render, or `backend/vercel.json` for Vercel. Set `DATABASE_URL` (e.g. Neon/Supabase) and `CORS_ORIGINS` (your deployed frontend URL) manually.
- **Frontend:** deploy via `frontend/vercel.json` on Vercel, or serve the Docker image (nginx) behind your platform of choice.

## Roles & Permissions

| Role | Permissions |
|---|---|
| Admin | Full access |
| Finance Manager | View financials, approve expenses/invoices, generate reports, view forecasts & AI insights, manage budgets, view audit log |
| Accountant | Manage transactions, invoices, expenses; reconcile; generate reports; manage customers/vendors |
| Viewer | View permitted data only |

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

## Author

Built by [Nabeha Gillani](https://github.com/nabehagillani).
