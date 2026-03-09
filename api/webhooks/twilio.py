"""LocalWeb AI — Twilio Webhooks (call status + recording)"""

from fastapi import APIRouter, Form
from typing import Optional

router = APIRouter()


@router.post("/call-status")
async def call_status(
    CallSid: str = Form(...),
    CallStatus: str = Form(...),
    CallDuration: Optional[str] = Form(None),
):
    """Twilio call status callback."""
    from workers.main import trigger_agent_task
    trigger_agent_task.delay("calling", CallSid, {
        "action": "status_update", "call_sid": CallSid,
        "status": CallStatus, "duration": CallDuration,
    })
    return {"status": "received"}


@router.post("/recording")
async def recording_ready(
    CallSid: str = Form(...),
    RecordingUrl: str = Form(...),
    RecordingSid: str = Form(...),
):
    """Twilio recording ready webhook — triggers transcription."""
    from workers.main import trigger_agent_task
    trigger_agent_task.delay("calling", CallSid, {
        "action": "handle_response",
        "call_sid": CallSid,
        "recording_url": RecordingUrl,
    })
    return {"status": "received"}
