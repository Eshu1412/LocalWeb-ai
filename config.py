"""
LocalWeb AI — Centralized Configuration
Loads all environment variables with validation using Pydantic Settings.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    # ── Application ─────────────────────────────────────────────
    APP_NAME: str = "LocalWeb AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False)
    ENVIRONMENT: str = Field(default="development")  # development | staging | production
    API_BASE_URL: str = Field(default="http://localhost:8000")

    # ── Database ────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./localweb.db",
        description="Database connection string (SQLite for dev, PostgreSQL for production)"
    )
    DB_POOL_SIZE: int = Field(default=20)
    DB_MAX_OVERFLOW: int = Field(default=10)

    # ── Redis ───────────────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://localhost:6379",
        description="Redis connection string for cache, streams, and DNC list"
    )

    # ── Authentication & Security ───────────────────────────────
    JWT_SECRET: str = Field(default="change-me-in-production-64-byte-hex")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_HOURS: int = Field(default=24)
    ENCRYPTION_KEY: str = Field(default="change-me-aes-256-key")

    # ── OpenAI ──────────────────────────────────────────────────
    OPENAI_API_KEY: str = Field(default="")
    OPENAI_MODEL: str = Field(default="gpt-4o")

    # ── Anthropic (QA Agent) ────────────────────────────────────
    ANTHROPIC_API_KEY: str = Field(default="")

    # ── ElevenLabs (TTS) ────────────────────────────────────────
    ELEVENLABS_API_KEY: str = Field(default="")
    ELEVENLABS_VOICE_ID: str = Field(default="")

    # ── Twilio (Voice Calls) ────────────────────────────────────
    TWILIO_ACCOUNT_SID: str = Field(default="")
    TWILIO_AUTH_TOKEN: str = Field(default="")
    TWILIO_PHONE_NUMBER: str = Field(default="")  # E.164 format

    # ── WhatsApp (Meta Cloud API) ───────────────────────────────
    WHATSAPP_ACCESS_TOKEN: str = Field(default="")
    WHATSAPP_PHONE_NUMBER_ID: str = Field(default="")
    WHATSAPP_VERIFY_TOKEN: str = Field(default="localweb-verify-token")

    # ── Google Places ───────────────────────────────────────────
    GOOGLE_PLACES_API_KEY: str = Field(default="")

    # ── SerpAPI ─────────────────────────────────────────────────
    SERPAPI_API_KEY: str = Field(default="")

    # ── Stripe (Payments) ───────────────────────────────────────
    STRIPE_SECRET_KEY: str = Field(default="")
    STRIPE_WEBHOOK_SECRET: str = Field(default="")
    STRIPE_PRICE_STARTER_MONTHLY: str = Field(default="")
    STRIPE_PRICE_SETUP_FEE: str = Field(default="")

    # ── Vercel (Deployment) ─────────────────────────────────────
    VERCEL_TOKEN: str = Field(default="")

    # ── Cloudflare (DNS) ────────────────────────────────────────
    CLOUDFLARE_API_TOKEN: str = Field(default="")
    CLOUDFLARE_ZONE_ID: str = Field(default="")

    # ── AWS S3 (File Storage) ───────────────────────────────────
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_S3_BUCKET: str = Field(default="localweb-assets")
    AWS_REGION: str = Field(default="us-east-1")

    # ── SendGrid (Email) ────────────────────────────────────────
    SENDGRID_API_KEY: str = Field(default="")

    # ── HubSpot (CRM) ──────────────────────────────────────────
    HUBSPOT_API_KEY: str = Field(default="")

    # ── Pinecone (Vector DB) ───────────────────────────────────
    PINECONE_API_KEY: str = Field(default="")
    PINECONE_ENVIRONMENT: str = Field(default="")
    PINECONE_INDEX_NAME: str = Field(default="faq-kb")

    # ── Celery ──────────────────────────────────────────────────
    CELERY_BROKER_URL: Optional[str] = None  # Defaults to REDIS_URL
    CELERY_RESULT_BACKEND: Optional[str] = None

    # ── Rate Limits ─────────────────────────────────────────────
    DISCOVERY_MAX_PER_MINUTE: int = Field(default=30)
    CALLING_MAX_PER_HOUR: int = Field(default=50)
    WHATSAPP_MAX_PER_HOUR: int = Field(default=200)
    CALL_WINDOW_START_HOUR: int = Field(default=9)   # 9 AM local
    CALL_WINDOW_END_HOUR: int = Field(default=20)     # 8 PM local
    OUTREACH_COOLDOWN_DAYS: int = Field(default=7)
    MAX_CALLS_PER_LEAD: int = Field(default=2)

    # ── Feature Flags ──────────────────────────────────────────
    CALLING_ENABLED: bool = Field(default=True)
    WHATSAPP_ENABLED: bool = Field(default=True)
    AUTO_DISCOVERY_ENABLED: bool = Field(default=False)
    SEO_AGENT_ENABLED: bool = Field(default=True)
    CRM_SYNC_ENABLED: bool = Field(default=True)

    # ── QA Thresholds ──────────────────────────────────────────
    QA_PERF_THRESHOLD: float = Field(default=0.8)
    QA_SEO_THRESHOLD: float = Field(default=0.8)
    QA_LLM_SCORE_MIN: int = Field(default=8)

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Singleton instance
settings = Settings()
