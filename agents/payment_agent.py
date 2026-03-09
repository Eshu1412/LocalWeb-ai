"""
LocalWeb AI — Payment Agent
Creates Stripe payment links, manages subscriptions, and handles webhooks.
"""

import stripe as stripe_lib

from agents.base_agent import BaseAgent
from config import settings
from db.models import BusinessLead


class PaymentAgent(BaseAgent):
    """Pipeline: stream:payment → PaymentAgent → stream:build (on success)"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        stripe_lib.api_key = settings.STRIPE_SECRET_KEY

    async def process(self, lead_id: str, payload: dict) -> dict:
        action = payload.get("action", "create_link")
        if action == "create_link":
            return await self.create_payment_link(lead_id, payload)
        elif action == "handle_success":
            return await self.handle_payment_success(payload["session_id"])
        return {"error": "Unknown action"}

    async def create_payment_link(self, lead_id: str, payload: dict) -> dict:
        """Create Stripe Checkout session and send link via WhatsApp."""
        name = payload.get("name", "Business Owner")
        phone = payload.get("phone", "")

        if not settings.STRIPE_SECRET_KEY:
            self.logger.warning("Stripe not configured — simulating")
            await self.update_lead_status(lead_id, "PAYMENT_LINK_SENT")
            return {"payment_url": f"https://checkout.stripe.com/sim_{lead_id[:8]}", "simulated": True}

        try:
            customer = stripe_lib.Customer.create(
                name=name, phone=phone, metadata={"lead_id": str(lead_id)}
            )

            line_items = []
            if settings.STRIPE_PRICE_STARTER_MONTHLY:
                line_items.append({"price": settings.STRIPE_PRICE_STARTER_MONTHLY, "quantity": 1})
            if settings.STRIPE_PRICE_SETUP_FEE:
                line_items.append({"price": settings.STRIPE_PRICE_SETUP_FEE, "quantity": 1})
            if not line_items:
                line_items = [{"price_data": {"currency": "usd", "product_data": {"name": "Starter Plan"}, "unit_amount": 4900, "recurring": {"interval": "month"}}, "quantity": 1}]

            session = stripe_lib.checkout.Session.create(
                customer=customer.id, payment_method_types=["card"],
                line_items=line_items, mode="subscription",
                success_url=f"{settings.API_BASE_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.API_BASE_URL}/cancel",
                metadata={"lead_id": str(lead_id)},
            )

            async with self.db() as db_session:
                lead = await db_session.get(BusinessLead, lead_id)
                if lead:
                    lead.stripe_customer_id = customer.id
                    await db_session.commit()

            await self.update_lead_status(lead_id, "PAYMENT_LINK_SENT")
            return {"payment_url": session.url, "customer_id": customer.id}
        except Exception as e:
            self.logger.error(f"Stripe error: {e}")
            raise

    async def handle_payment_success(self, session_id: str) -> dict:
        """Called by Stripe webhook — updates lead and triggers build."""
        try:
            session = stripe_lib.checkout.Session.retrieve(session_id)
            lead_id = session.metadata.get("lead_id")
            if not lead_id:
                return {"error": "No lead_id found"}

            from datetime import datetime, timezone
            async with self.db() as db_session:
                lead = await db_session.get(BusinessLead, lead_id)
                if lead:
                    lead.status = "PAID"
                    lead.paid_at = datetime.now(timezone.utc)
                    lead.stripe_subscription_id = session.subscription
                    lead.plan = "starter"
                    await db_session.commit()

                    await self.emit_event("stream:build", lead_id, {
                        "name": lead.name, "category": lead.category,
                        "phone": lead.phone, "preview_url": lead.preview_url,
                    })
            return {"lead_id": lead_id, "status": "paid"}
        except Exception as e:
            self.logger.error(f"Payment success handling failed: {e}")
            raise
