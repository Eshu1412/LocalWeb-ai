"""
LocalWeb AI — FastAPI Application Entry Point
Main API server with CORS, auth middleware, and route registration.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle events."""
    # Startup — import models so Base.metadata knows all tables
    from db.database import engine, Base
    import db.models  # noqa: F401 — registers all ORM models
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Automated AI Agent Platform for Local Business Websites",
    lifespan=lifespan,
)

# ── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://dashboard.localweb.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Register Routes ────────────────────────────────────────
from api.routes import leads, pipeline, sites, templates
from api.webhooks import twilio, stripe_wh, whatsapp

app.include_router(leads.router, prefix="/api", tags=["Leads"])
app.include_router(pipeline.router, prefix="/api", tags=["Pipeline"])
app.include_router(sites.router, prefix="/api", tags=["Sites"])
app.include_router(templates.router, prefix="/api", tags=["Templates"])
app.include_router(twilio.router, prefix="/webhooks/twilio", tags=["Webhooks"])
app.include_router(stripe_wh.router, prefix="/webhooks/stripe", tags=["Webhooks"])
app.include_router(whatsapp.router, prefix="/webhooks/whatsapp", tags=["Webhooks"])


# ── Health Check ────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
