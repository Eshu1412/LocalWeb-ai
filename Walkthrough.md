# LocalWeb AI — Project Walkthrough

## What Was Built

A complete **multi-agent SaaS platform** (70 files) that autonomously discovers local businesses without websites, builds them sample sites, reaches out via AI voice calls and WhatsApp, processes payments, deploys production sites, and manages the full client lifecycle.

---

## Architecture Overview

```mermaid
graph LR
    A[Orchestrator] --> B[Discovery Agent]
    B --> C[Verification Agent]
    C --> D[Sample Builder]
    D --> E[Calling Agent]
    D --> F[WhatsApp Agent]
    E --> G[Negotiation Agent]
    F --> G
    G --> H[Payment Agent]
    H --> I[Builder Agent]
    I --> J[QA Agent]
    J --> K[SEO Agent]
    K --> L[CRM Agent]
```

---

## Project Structure

| Component | Files | Description |
|-----------|-------|-------------|
| **Agents** | 13 files | Base agent + 12 specialized agents |
| **API** | 8 files | FastAPI routes, webhooks, main app |
| **Database** | 4 files | Models, async engine, Alembic |
| **Workers** | 2 files | Celery task routing |
| **Prompts** | 6 files | AI prompt templates |
| **CLI Tools** | 15 files | 14 management scripts |
| **Dashboard** | 11 files | Next.js 14 + Tailwind CSS |
| **Infrastructure** | 5 files | Docker, config, env |
| **Total** | **70 files** | |

---

## Key Components

### 12 AI Agents (Redis Streams Pipeline)
All agents inherit from [base_agent.py](file:///c:/Users/maury/OneDrive/Desktop/CODE/CoreProject/localweb-ai/agents/base_agent.py) which provides Redis Streams pub/sub, PostgreSQL state management, retry logic, and DNC checks.

### FastAPI Backend
- [main.py](file:///c:/Users/maury/OneDrive/Desktop/CODE/CoreProject/localweb-ai/api/main.py) — Entry point with CORS and route registration
- REST API for leads, pipeline stats, sites, and templates
- Webhook handlers for Twilio, Stripe, and WhatsApp

### Next.js Admin Dashboard
Dark-themed glassmorphism UI with 6 pages:
- **Pipeline** — Stats cards, funnel chart, activity feed
- **Leads** — Searchable data table with action buttons
- **Agents** — 12-card grid with status and controls
- **Analytics** — KPIs and unit economics
- **Settings** — API integrations and feature flags

### 14 CLI Tools
Production-grade management scripts for setup, key management, health checks, database admin, agent control, logging, DNC lists, secrets rotation, deployment, diagnostics, billing, and site management.

---

## Google Stitch UI Designs

3 premium dark-themed dashboard screens generated via Stitch MCP:

**Stitch Project:** [LocalWeb AI Dashboard](https://stitch.withgoogle.com/projects/16891475527969972411)

| Screen | Description |
|--------|-------------|
| Main Dashboard | Stats grid, pipeline funnel, activity feed |
| Agents Configuration | 12-card grid with controls |
| Leads Management | Data table with filters and actions |

---

## Getting Started

```bash
# 1. Clone and configure
cd localweb-ai
cp .env.example .env
# Edit .env with your API keys

# 2. Start infrastructure
docker compose up -d postgres redis

# 3. Install Python deps
pip install -r requirements.txt

# 4. Run API server
uvicorn api.main:app --reload --port 8000

# 5. Start Celery worker
celery -A workers.main.app worker --loglevel=info

# 6. Install & run dashboard
cd dashboard && npm install && npm run dev
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy |
| Queue | Celery, Redis Streams |
| Database | PostgreSQL, Redis |
| AI | OpenAI GPT-4o, ElevenLabs, Whisper |
| Comms | Twilio, Meta WhatsApp Cloud API |
| Payments | Stripe |
| Frontend | Next.js 14, Tailwind CSS |
| Deploy | Docker, Vercel, Cloudflare |
