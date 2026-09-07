from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.session import Base, engine
from app import models  # noqa: F401 ensures all models are registered on Base
from app.routes import (
    auth, dashboard, transactions, expenses, invoices, receivables, payables,
    reconciliation, budgets, reports, forecasting, insights, ai_assistant,
    notifications, audit, settings as settings_routes,
)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME}


for router in [
    auth.router, dashboard.router, transactions.router, expenses.router, invoices.router,
    receivables.router, payables.router, reconciliation.router, budgets.router, reports.router,
    forecasting.router, insights.router, ai_assistant.router, notifications.router, audit.router,
    settings_routes.router,
]:
    app.include_router(router)
