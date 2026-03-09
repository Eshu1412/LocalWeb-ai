"""
LocalWeb AI — CRM Agent
Manages contact data, follow-ups, and email sequences via HubSpot/SendGrid.
"""

import httpx
from agents.base_agent import BaseAgent
from config import settings


class CRMAgent(BaseAgent):
    """Pipeline: stream:crm → CRMAgent (final stage)"""

    async def process(self, lead_id: str, payload: dict) -> dict:
        """Handle CRM operations for a live client."""
        self.logger.info(f"CRM processing for lead {lead_id}")

        results = {}

        # 1. Send welcome email
        results["welcome_email"] = await self._send_welcome_email(payload)

        # 2. Create/update CRM contact
        results["crm_contact"] = await self._upsert_crm_contact(payload)

        # 3. Schedule 30-day check-in
        results["followup"] = await self._schedule_followup(lead_id, 30)

        # 4. Flag for upsell sequence
        results["upsell"] = await self._flag_for_upsell(lead_id, payload)

        return results

    async def _send_welcome_email(self, payload: dict) -> dict:
        """Send welcome email via SendGrid."""
        email = payload.get("email")
        if not email or not settings.SENDGRID_API_KEY:
            return {"sent": False, "reason": "no_email_or_api_key"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "personalizations": [{"to": [{"email": email}]}],
                        "from": {"email": "hello@localweb.ai", "name": "LocalWeb AI"},
                        "subject": f"🎉 Your website is live! — {payload.get('name', '')}",
                        "content": [{
                            "type": "text/html",
                            "value": (
                                f"<h1>Welcome to LocalWeb AI!</h1>"
                                f"<p>Your website for {payload.get('name', '')} is now live at "
                                f"<a href='{payload.get('live_url', '')}'>{payload.get('domain', '')}</a>.</p>"
                                f"<p>We'll check in with you in 30 days to make sure everything is perfect.</p>"
                            ),
                        }],
                    },
                )
            return {"sent": True}
        except Exception as e:
            self.logger.error(f"Welcome email failed: {e}")
            return {"sent": False, "error": str(e)}

    async def _upsert_crm_contact(self, payload: dict) -> dict:
        """Create or update contact in HubSpot."""
        if not settings.HUBSPOT_API_KEY:
            return {"synced": False, "reason": "hubspot_not_configured"}

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(
                    "https://api.hubapi.com/crm/v3/objects/contacts",
                    headers={"Authorization": f"Bearer {settings.HUBSPOT_API_KEY}"},
                    json={
                        "properties": {
                            "firstname": payload.get("name", "").split()[0] if payload.get("name") else "",
                            "phone": payload.get("phone", ""),
                            "email": payload.get("email", ""),
                            "company": payload.get("name", ""),
                            "website": payload.get("live_url", ""),
                        }
                    },
                )
            return {"synced": True}
        except Exception as e:
            self.logger.warning(f"HubSpot sync failed: {e}")
            return {"synced": False}

    async def _schedule_followup(self, lead_id: str, days: int) -> dict:
        """Schedule a follow-up check-in via Redis delayed task."""
        await self.redis.set(f"followup:{lead_id}", days, ex=days * 86400)
        return {"scheduled": True, "days": days}

    async def _flag_for_upsell(self, lead_id: str, payload: dict) -> dict:
        """Flag lead for upsell sequence based on plan."""
        plan = payload.get("plan", "starter")
        if plan == "starter":
            await self.redis.sadd("upsell:business_plan", str(lead_id))
            return {"flagged": True, "target_plan": "business"}
        return {"flagged": False}
