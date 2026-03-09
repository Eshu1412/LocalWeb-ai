"""LocalWeb AI — Deployed Sites & Templates Routes"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import DeployedSite

router = APIRouter()


@router.get("/sites/{domain}")
async def get_site(domain: str, db: AsyncSession = Depends(get_db)):
    """Get deployed site info by domain."""
    result = await db.execute(select(DeployedSite).where(DeployedSite.domain == domain))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return {
        "domain": site.domain, "status": site.status,
        "template": site.template_used,
        "lighthouse": {"perf": site.lighthouse_perf, "seo": site.lighthouse_seo, "a11y": site.lighthouse_a11y},
        "deployed_at": site.deployed_at.isoformat() if site.deployed_at else None,
    }


@router.post("/sites/{domain}/redeploy")
async def redeploy_site(domain: str, db: AsyncSession = Depends(get_db)):
    """Trigger site rebuild."""
    result = await db.execute(select(DeployedSite).where(DeployedSite.domain == domain))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    from workers.main import trigger_agent_task
    trigger_agent_task.delay("builder", str(site.lead_id), {"action": "rebuild"})
    return {"status": "redeploy_queued", "domain": domain}
