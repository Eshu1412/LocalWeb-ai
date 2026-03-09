"""LocalWeb AI — Pipeline Stats & Discovery Trigger Routes"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import BusinessLead

router = APIRouter()


class DiscoverRequest(BaseModel):
    area: str
    categories: list[str] = ["restaurant", "salon", "clinic", "gym", "cafe"]


@router.post("/discover")
async def trigger_discovery(req: DiscoverRequest):
    """Trigger discovery for an area + categories."""
    from workers.main import trigger_agent_task
    for cat in req.categories:
        trigger_agent_task.delay("discovery", "orchestrator", {"area": req.area, "category": cat})
    return {"status": "discovery_queued", "area": req.area, "categories": len(req.categories)}


@router.get("/pipeline/stats")
async def pipeline_stats(db: AsyncSession = Depends(get_db)):
    """Dashboard metrics: leads, conversions, MRR."""
    result = await db.execute(
        select(BusinessLead.status, func.count(BusinessLead.id)).group_by(BusinessLead.status)
    )
    stats = {status: count for status, count in result.all()}
    total = sum(stats.values())
    paid = stats.get("PAID", 0) + stats.get("LIVE", 0)

    return {
        "total_leads": total,
        "by_status": stats,
        "no_website": stats.get("NO_WEBSITE", 0),
        "paid": paid,
        "live": stats.get("LIVE", 0),
        "conversion_rate": round(paid / max(stats.get("NO_WEBSITE", 0), 1) * 100, 2),
        "estimated_mrr": paid * 49,  # Starter plan
    }
