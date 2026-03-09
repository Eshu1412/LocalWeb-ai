"""LocalWeb AI — Website Templates Routes"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

AVAILABLE_TEMPLATES = [
    {"id": "restaurant", "name": "Restaurant / Café", "pages": 5, "features": ["menu", "reservation", "gallery"]},
    {"id": "salon", "name": "Salon / Spa", "pages": 5, "features": ["services", "booking", "gallery"]},
    {"id": "clinic", "name": "Doctor / Clinic", "pages": 5, "features": ["services", "appointment", "staff"]},
    {"id": "gym", "name": "Gym / Fitness", "pages": 5, "features": ["classes", "membership", "trainers"]},
    {"id": "auto_repair", "name": "Auto Repair", "pages": 5, "features": ["services", "quote", "gallery"]},
    {"id": "service_provider", "name": "Home Services", "pages": 5, "features": ["services", "quote", "areas"]},
    {"id": "retail", "name": "Retail Store", "pages": 5, "features": ["products", "location", "hours"]},
    {"id": "general", "name": "General Business", "pages": 5, "features": ["about", "services", "contact"]},
]


@router.get("/templates")
async def list_templates():
    """List all available website templates."""
    return {"templates": AVAILABLE_TEMPLATES, "total": len(AVAILABLE_TEMPLATES)}


class PreviewRequest(BaseModel):
    name: str
    category: str
    address: str = ""


@router.post("/templates/preview")
async def generate_preview(req: PreviewRequest):
    """Generate instant preview for any business."""
    from workers.main import trigger_agent_task
    trigger_agent_task.delay("sample_builder", "manual", {
        "name": req.name, "category": req.category, "address": req.address,
    })
    return {"status": "preview_queued", "name": req.name, "category": req.category}
