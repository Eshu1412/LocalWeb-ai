"""
LocalWeb AI — Base Agent Class
Abstract base for all AI agents. Provides Redis Streams pub/sub,
PostgreSQL session access, structured logging, and event emission.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import BusinessLead, PipelineEvent


class BaseAgent(ABC):
    """
    Abstract base class all LocalWeb AI agents inherit from.

    Provides:
        - Redis Streams event publishing
        - PostgreSQL session for lead state updates
        - Structured logging per agent
        - Retry + error handling helpers
    """

    # Max retries for external API calls
    MAX_RETRIES = 3
    RETRY_BACKOFF_BASE = 2  # seconds

    def __init__(self, redis_client: redis.Redis, db_session_factory):
        self.redis = redis_client
        self.db = db_session_factory  # async_sessionmaker
        self.agent_name = self.__class__.__name__
        self.logger = logging.getLogger(self.agent_name)

    @abstractmethod
    async def process(self, lead_id: str, payload: dict) -> dict:
        """
        Main processing method — each agent implements its own logic.

        Args:
            lead_id: UUID of the business lead being processed
            payload: Dict with lead data and any upstream context

        Returns:
            Dict with processing results
        """
        pass

    # ── Event Emission (Redis Streams) ─────────────────────
    async def emit_event(self, stream: str, lead_id: str, data: dict) -> str:
        """
        Publish an event to a Redis Stream for downstream agents.

        Args:
            stream: Stream name (e.g. 'stream:verify', 'stream:outreach')
            lead_id: UUID of the associated lead
            data: Event payload

        Returns:
            Redis message ID
        """
        message = {
            "lead_id": str(lead_id),
            "agent": self.agent_name,
            "data": json.dumps(data, default=str),
        }
        msg_id = await self.redis.xadd(stream, message)
        self.logger.info(f"Emitted event to {stream} for lead {lead_id}")
        return msg_id

    # ── Lead State Updates ─────────────────────────────────
    async def update_lead_status(
        self, lead_id: str, status: str, notes: str = ""
    ) -> None:
        """
        Update a lead's pipeline status in PostgreSQL and log the event.

        Args:
            lead_id: UUID of the lead
            status: New status string (e.g. 'VERIFIED', 'CALL_INITIATED')
            notes: Optional notes about the status change
        """
        async with self.db() as session:
            lead = await session.get(BusinessLead, lead_id)
            if lead:
                old_status = lead.status
                lead.status = status
                if notes:
                    lead.notes = notes

                # Log the pipeline event
                event = PipelineEvent(
                    lead_id=lead_id,
                    agent=self.agent_name,
                    event=f"STATUS_CHANGE: {old_status} → {status}",
                    payload={"old_status": old_status, "new_status": status, "notes": notes},
                )
                session.add(event)
                await session.commit()
                self.logger.info(
                    f"Lead {lead_id}: {old_status} → {status}"
                )
            else:
                self.logger.error(f"Lead {lead_id} not found for status update")

    # ── Lead Retrieval ─────────────────────────────────────
    async def get_lead(self, lead_id: str) -> Optional[BusinessLead]:
        """Fetch a lead by ID from PostgreSQL."""
        async with self.db() as session:
            return await session.get(BusinessLead, lead_id)

    async def get_lead_by_phone(self, phone: str) -> Optional[BusinessLead]:
        """Fetch a lead by phone number."""
        from sqlalchemy import select
        async with self.db() as session:
            result = await session.execute(
                select(BusinessLead).where(BusinessLead.phone == phone)
            )
            return result.scalar_one_or_none()

    # ── DNC Check ──────────────────────────────────────────
    async def is_on_dnc(self, phone: str) -> bool:
        """Check if a phone number is on the Do-Not-Contact list (Redis set)."""
        return await self.redis.sismember("dnc:phones", phone)

    # ── Retry Helper ───────────────────────────────────────
    async def retry_with_backoff(self, func, *args, max_retries=None, **kwargs):
        """
        Execute a function with exponential backoff retry.

        Args:
            func: Async function to call
            max_retries: Override default MAX_RETRIES
        """
        retries = max_retries or self.MAX_RETRIES
        for attempt in range(retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == retries - 1:
                    self.logger.error(
                        f"All {retries} retries exhausted for {func.__name__}: {e}"
                    )
                    raise
                wait = self.RETRY_BACKOFF_BASE ** attempt
                self.logger.warning(
                    f"Retry {attempt + 1}/{retries} for {func.__name__} "
                    f"after {wait}s: {e}"
                )
                await asyncio.sleep(wait)

    # ── Stream Listener ────────────────────────────────────
    async def listen(self, stream: str, group: str = None):
        """
        Listen to a Redis Stream for incoming events.
        Creates consumer group if it doesn't exist.

        Args:
            stream: Stream name to listen on
            group: Consumer group name (defaults to agent name)
        """
        group = group or self.agent_name
        consumer = f"{group}-worker-1"

        # Create consumer group if not exists
        try:
            await self.redis.xgroup_create(stream, group, id="0", mkstream=True)
        except redis.ResponseError:
            pass  # Group already exists

        self.logger.info(f"Listening on stream '{stream}' as group '{group}'")

        while True:
            try:
                messages = await self.redis.xreadgroup(
                    group, consumer, {stream: ">"}, count=10, block=5000
                )
                for _, entries in messages:
                    for msg_id, data in entries:
                        lead_id = data.get(b"lead_id", data.get("lead_id", ""))
                        payload = json.loads(
                            data.get(b"data", data.get("data", "{}"))
                        )
                        if isinstance(lead_id, bytes):
                            lead_id = lead_id.decode()

                        try:
                            await self.process(lead_id, payload)
                            await self.redis.xack(stream, group, msg_id)
                        except Exception as e:
                            self.logger.error(
                                f"Error processing {msg_id} for lead {lead_id}: {e}",
                                exc_info=True,
                            )
            except asyncio.CancelledError:
                self.logger.info("Listener cancelled, shutting down...")
                break
            except Exception as e:
                self.logger.error(f"Stream listener error: {e}", exc_info=True)
                await asyncio.sleep(5)
