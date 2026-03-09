"""
LocalWeb AI — Celery Worker Configuration
Task definitions for all agents with async support.
"""

from celery import Celery
from config import settings

# ── Celery App ──────────────────────────────────────────────
app = Celery(
    "localweb",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="default",
    task_routes={
        "workers.main.trigger_agent_task": {"queue": "agents"},
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)


@app.task(name="workers.main.trigger_agent_task", bind=True, max_retries=3)
def trigger_agent_task(self, agent_name: str, lead_id: str, payload: dict):
    """
    Generic task that routes work to the appropriate agent.
    Called by API routes and webhooks to trigger async agent processing.
    """
    import asyncio
    import redis as sync_redis

    from db.database import async_session

    # Create Redis client
    redis_client = sync_redis.from_url(settings.REDIS_URL)

    # Agent registry
    agent_map = {
        "discovery": "agents.discovery_agent.DiscoveryAgent",
        "verification": "agents.verification_agent.VerificationAgent",
        "sample_builder": "agents.sample_builder.SampleBuilderAgent",
        "calling": "agents.calling_agent.CallingAgent",
        "whatsapp": "agents.whatsapp_agent.WhatsAppAgent",
        "negotiation": "agents.negotiation_agent.NegotiationAgent",
        "payment": "agents.payment_agent.PaymentAgent",
        "builder": "agents.builder_agent.BuilderAgent",
        "qa": "agents.qa_agent.QAAgent",
        "seo": "agents.seo_agent.SEOAgent",
        "crm": "agents.crm_agent.CRMAgent",
        "orchestrator": "agents.orchestrator.OrchestratorAgent",
    }

    agent_path = agent_map.get(agent_name)
    if not agent_path:
        raise ValueError(f"Unknown agent: {agent_name}")

    # Dynamically import and instantiate agent
    module_path, class_name = agent_path.rsplit(".", 1)
    import importlib
    module = importlib.import_module(module_path)
    agent_class = getattr(module, class_name)

    # Run async agent in event loop
    async def run():
        import redis.asyncio as aioredis
        async_redis = aioredis.from_url(settings.REDIS_URL)
        agent = agent_class(async_redis, async_session)
        try:
            result = await agent.process(lead_id, payload)
            return result
        finally:
            await async_redis.close()

    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(run())
        return result
    except Exception as exc:
        self.retry(exc=exc, countdown=2 ** self.request.retries)
    finally:
        loop.close()
