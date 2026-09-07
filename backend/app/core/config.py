"""
Central application configuration.
Reads from environment variables so the same code runs against
PostgreSQL in production and SQLite for local/demo runs.
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Finance Automation & AI Decision Support"
    ENV: str = os.getenv("ENV", "development")

    # Default to SQLite for zero-setup local runs. In production set:
    # DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./finance.db")

    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "CHANGE_ME_IN_PRODUCTION")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 hours

    # Comma-separated list of allowed frontend origins, e.g.
    # "https://your-app.vercel.app,http://localhost:5173" — set this env
    # var on the deployed backend once you know your frontend's real URL.
    # NOTE: kept as a plain string field (not `list`) on purpose —
    # pydantic-settings expects list-typed env vars to be valid JSON
    # (e.g. '["a","b"]'), and crashes on a plain comma-separated string
    # or "*". See the cors_origins_list property below for the parsed form.
    CORS_ORIGINS: str = os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    )

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # Business rules
    LOW_CASH_THRESHOLD_DAYS: int = 30
    UNUSUAL_EXPENSE_STDEV_MULTIPLIER: float = 2.0

    # File uploads (receipts, etc.) — stored on local disk by default.
    # On Vercel's serverless filesystem, only /tmp is writable, and even
    # that doesn't persist between invocations — receipt uploads work
    # per-request there but won't survive a cold start. Point this at a
    # mounted volume / object-storage-backed path for real persistence.
    UPLOAD_DIR: str = os.getenv(
        "UPLOAD_DIR", "/tmp/uploads" if os.getenv("VERCEL") else "./uploads"
    )
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB

    # Same reasoning as CORS_ORIGINS: kept as a comma-separated string
    # rather than `list` so it can never crash Settings() if someone
    # ever sets ALLOWED_RECEIPT_TYPES as a plain env var.
    ALLOWED_RECEIPT_TYPES_RAW: str = os.getenv(
        "ALLOWED_RECEIPT_TYPES", "image/jpeg,image/png,image/webp,application/pdf"
    )

    @property
    def ALLOWED_RECEIPT_TYPES(self) -> list[str]:
        return [t.strip() for t in self.ALLOWED_RECEIPT_TYPES_RAW.split(",") if t.strip()]

    # Optional: set to enable real LLM-backed AI Assistant responses.
    # Falls back to the rule-based assistant when unset.
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")

    class Config:
        env_file = ".env"


settings = Settings()
