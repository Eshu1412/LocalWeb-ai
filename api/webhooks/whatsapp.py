"""LocalWeb AI — WhatsApp Incoming Message Webhook"""

from fastapi import APIRouter, Request, Query

from config import settings

router = APIRouter()


@router.get("/incoming")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", default=""),
    hub_token: str = Query(alias="hub.verify_token", default=""),
    hub_challenge: str = Query(alias="hub.challenge", default=""),
):
    """Meta webhook verification challenge."""
    if hub_mode == "subscribe" and hub_token == settings.WHATSAPP_VERIFY_TOKEN:
        return int(hub_challenge)
    return {"error": "Verification failed"}


@router.post("/incoming")
async def incoming_message(request: Request):
    """Handle incoming WhatsApp messages."""
    body = await request.json()

    for entry in body.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            for msg in value.get("messages", []):
                phone = msg.get("from", "")
                text = msg.get("text", {}).get("body", "")
                button = msg.get("interactive", {}).get("button_reply", {})
                button_id = button.get("id") if button else None

                from workers.main import trigger_agent_task
                trigger_agent_task.delay("whatsapp", phone, {
                    "action": "handle_reply",
                    "phone": phone,
                    "message": text or button.get("title", ""),
                    "button_id": button_id,
                })

    return {"status": "received"}
