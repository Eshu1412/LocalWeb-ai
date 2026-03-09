"""LocalWeb AI — Stripe Payment Webhooks"""

import json
try:
    import stripe
except ImportError:
    stripe = None  # type: ignore
from fastapi import APIRouter, Request, HTTPException

from config import settings

router = APIRouter()


@router.post("/payment")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    if settings.STRIPE_WEBHOOK_SECRET:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            raise HTTPException(status_code=400, detail="Invalid signature")
    else:
        event = json.loads(payload)

    event_type = event.get("type", "")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        from workers.main import trigger_agent_task
        trigger_agent_task.delay("payment", session.get("metadata", {}).get("lead_id", ""), {
            "action": "handle_success", "session_id": session["id"],
        })
    elif event_type == "customer.subscription.deleted":
        sub = event["data"]["object"]
        # Handle churn
        pass

    return {"received": True}
