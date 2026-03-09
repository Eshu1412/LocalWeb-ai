"""
LocalWeb AI — Orchestrator Agent
Master controller that schedules discovery runs, monitors the pipeline,
and handles inter-agent coordination via Redis Streams.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from agents.base_agent import BaseAgent
from config import settings


class OrchestratorAgent(BaseAgent):
    """
    Master pipeline controller.

    Responsibilities:
        - Schedule periodic discovery runs by area + category
        - Monitor agent health and queue depths
        - Handle pipeline stalls (leads stuck in a status too long)
        - Coordinate recovery and re-processing of failed leads
    """

    # Default discovery targets
    DEFAULT_CATEGORIES = [
        "restaurant", "salon", "barbershop", "bakery", "cafe",
        "auto repair", "dentist", "clinic", "gym", "plumber",
        "electrician", "pet store", "florist", "laundry", "pharmacy",
    ]

    async def process(self, lead_id: str, payload: dict) -> dict:
        """Process orchestration commands."""
        command = payload.get("command", "discover")

        if command == "discover":
            return await self.run_discovery(
                area=payload.get("area", ""),
                categories=payload.get("categories", self.DEFAULT_CATEGORIES),
            )
        elif command == "check_stalled":
            return await self.check_stalled_leads()
        elif command == "pipeline_stats":
            return await self.get_pipeline_stats()
        else:
            self.logger.warning(f"Unknown orchestrator command: {command}")
            return {"error": f"Unknown command: {command}"}

    async def run_discovery(self, area: str, categories: list[str]) -> dict:
        """
        Trigger discovery for an area across multiple categories.
        Emits one event per category to the discovery stream.
        """
        self.logger.info(f"Starting discovery run for area='{area}', {len(categories)} categories")
        events_emitted = 0

        for category in categories:
            await self.emit_event("stream:discover", "orchestrator", {
                "area": area,
                "category": category,
                "triggered_at": datetime.now(timezone.utc).isoformat(),
            })
            events_emitted += 1

        self.logger.info(f"Emitted {events_emitted} discovery tasks for area '{area}'")
        return {"area": area, "categories": len(categories), "events_emitted": events_emitted}

    async def check_stalled_leads(self, hours: int = 24) -> dict:
        """
        Find leads stuck in intermediate statuses for too long.
        Re-queues them or escalates to human review.
        """
        from sqlalchemy import select, func
        from db.models import BusinessLead

        stalled_statuses = [
            "SAMPLE_BUILDING", "CALL_INITIATED", "WHATSAPP_SENT",
            "PAYMENT_LINK_SENT", "BUILDING", "QA_IN_PROGRESS",
        ]
        cutoff = datetime.now(timezone.utc).replace(
            hour=datetime.now(timezone.utc).hour - hours
        )
        stalled = []

        async with self.db() as session:
            for status in stalled_statuses:
                result = await session.execute(
                    select(BusinessLead)
                    .where(BusinessLead.status == status)
                    .where(BusinessLead.updated_at < cutoff)
                )
                leads = result.scalars().all()
                for lead in leads:
                    stalled.append({
                        "lead_id": str(lead.id),
                        "name": lead.name,
                        "status": lead.status,
                        "stuck_since": lead.updated_at.isoformat(),
                    })
                    self.logger.warning(
                        f"Stalled lead: {lead.name} in {lead.status} since {lead.updated_at}"
                    )

        return {"stalled_count": len(stalled), "leads": stalled}

    async def get_pipeline_stats(self) -> dict:
        """Get current pipeline statistics for the dashboard."""
        from sqlalchemy import select, func
        from db.models import BusinessLead

        async with self.db() as session:
            result = await session.execute(
                select(BusinessLead.status, func.count(BusinessLead.id))
                .group_by(BusinessLead.status)
            )
            stats = {status: count for status, count in result.all()}

        return {
            "total_leads": sum(stats.values()),
            "by_status": stats,
            "conversion_rate": (
                stats.get("PAID", 0) / max(stats.get("NO_WEBSITE", 0), 1) * 100
            ),
        }
