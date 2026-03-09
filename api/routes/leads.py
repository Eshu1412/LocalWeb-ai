"""
LocalWeb AI — Leads API Routes
CRUD endpoints for business leads with filtering and pagination.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import BusinessLead, PipelineEvent

router = APIRouter()


@router.get("/leads")
async def list_leads(
    status: Optional[str] = None,
    category: Optional[str] = None,
    area: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """List all leads with filters and pagination."""
    query = select(BusinessLead).order_by(BusinessLead.created_at.desc())

    if status:
        query = query.where(BusinessLead.status == status)
    if category:
        query = query.where(BusinessLead.category == category)
    if area:
        query = query.where(BusinessLead.area.ilike(f"%{area}%"))
    if search:
        query = query.where(BusinessLead.name.ilike(f"%{search}%"))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    # Paginate
    offset = (page - 1) * per_page
    result = await db.execute(query.offset(offset).limit(per_page))
    leads = result.scalars().all()

    return {
        "leads": [_lead_to_dict(l) for l in leads],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page,
    }


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single lead with full pipeline history."""
    lead = await db.get(BusinessLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    events = await db.execute(
        select(PipelineEvent)
        .where(PipelineEvent.lead_id == lead_id)
        .order_by(PipelineEvent.timestamp.desc())
    )

    return {
        **_lead_to_dict(lead),
        "events": [
            {"agent": e.agent, "event": e.event, "timestamp": e.timestamp.isoformat(), "payload": e.payload}
            for e in events.scalars().all()
        ],
    }


@router.post("/leads/{lead_id}/call")
async def trigger_call(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Manually trigger AI call for a lead."""
    lead = await db.get(BusinessLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    # Emit to calling stream via Celery task
    from workers.main import trigger_agent_task
    trigger_agent_task.delay("calling", str(lead_id), {"action": "initiate_call", "phone": lead.phone, "name": lead.name, "category": lead.category, "preview_url": lead.preview_url or ""})
    return {"status": "call_queued", "lead_id": str(lead_id)}


@router.post("/leads/{lead_id}/whatsapp")
async def trigger_whatsapp(lead_id: UUID, db: AsyncSession = Depends(get_db)):
    """Manually trigger WhatsApp outreach for a lead."""
    lead = await db.get(BusinessLead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    from workers.main import trigger_agent_task
    trigger_agent_task.delay("whatsapp", str(lead_id), {"action": "send_pitch", "phone": lead.phone, "name": lead.name, "category": lead.category, "preview_url": lead.preview_url or ""})
    return {"status": "whatsapp_queued", "lead_id": str(lead_id)}


def _lead_to_dict(lead: BusinessLead) -> dict:
    return {
        "id": str(lead.id),
        "name": lead.name,
        "phone": lead.phone,
        "email": lead.email,
        "address": lead.address,
        "category": lead.category,
        "area": lead.area,
        "status": lead.status,
        "has_website": lead.has_website,
        "preview_url": lead.preview_url,
        "live_url": lead.live_url,
        "domain": lead.domain,
        "plan": lead.plan,
        "source": lead.source,
        "created_at": lead.created_at.isoformat() if lead.created_at else None,
        "updated_at": lead.updated_at.isoformat() if lead.updated_at else None,
    }
