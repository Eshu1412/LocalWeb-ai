"""
LocalWeb AI — WhatsApp Agent
Sends personalized WhatsApp pitches via Meta Business Cloud API.
Handles incoming replies and routes to appropriate next agent.
"""

import httpx

from agents.base_agent import BaseAgent
from config import settings
from db.models import WhatsAppMessage


class WhatsAppAgent(BaseAgent):
    """
    WhatsApp outreach and conversation handler.

    Pipeline: stream:outreach → WhatsAppAgent → stream:negotiate / stream:payment
    """

    META_API_BASE = "https://graph.facebook.com/v18.0"

    async def process(self, lead_id: str, payload: dict) -> dict:
        """Route to send_pitch or handle_reply based on action."""
        action = payload.get("action", "send_pitch")
        if action == "send_pitch":
            return await self.send_pitch(lead_id, payload)
        elif action == "handle_reply":
            return await self.handle_reply(
                payload["phone"], payload["message"], payload.get("button_id")
            )
        return {"error": "Unknown action"}

    async def send_pitch(self, lead_id: str, payload: dict) -> dict:
        """
        Send a personalized WhatsApp pitch message.

        Steps:
            1. Send screenshot of sample site as image message
            2. Send interactive button message with pricing and CTA
        """
        phone = payload.get("phone", "")
        if not phone:
            return {"error": "No phone number"}

        if not settings.WHATSAPP_ENABLED:
            return {"skipped": True, "reason": "whatsapp_disabled"}

        # Check DNC
        if await self.is_on_dnc(phone):
            await self.update_lead_status(lead_id, "NOT_INTERESTED", "On DNC list")
            return {"skipped": True, "reason": "dnc"}

        preview_url = payload.get("preview_url", "")
        screenshot_url = payload.get("screenshot_url", "")
        business_name = payload.get("name", "your business")

        # 1. Send image with caption
        await self._send_image(
            phone=phone,
            image_url=screenshot_url,
            caption=(
                f"👋 Hi! We built a FREE sample website for {business_name}.\n\n"
                f"🌐 Check it out: {preview_url}\n\n"
                f"Interested? Reply YES!"
            ),
            lead_id=lead_id,
        )

        # 2. Send interactive button message
        await self._send_interactive(
            phone=phone,
            body=(
                f"We can get {business_name} online in 24 hours "
                f"starting at just $49/month. No design skills needed — "
                f"we handle everything!"
            ),
            buttons=[
                {"id": "interested", "title": "Yes, I'm Interested!"},
                {"id": "pricing", "title": "See Pricing"},
                {"id": "not_now", "title": "Not Right Now"},
            ],
            lead_id=lead_id,
        )

        await self.update_lead_status(lead_id, "WHATSAPP_SENT")
        return {"status": "sent", "phone": phone}

    async def handle_reply(self, phone: str, message: str, button_id: str = None) -> dict:
        """
        Handle an incoming WhatsApp reply from a business owner.

        Routes:
            - 'interested' / 'yes' → Payment Agent
            - 'pricing' → Send pricing details
            - 'not_now' → Mark as not interested + schedule re-engage
            - Other → Negotiation Agent for AI response
        """
        lead = await self.get_lead_by_phone(phone)
        if not lead:
            self.logger.warning(f"No lead found for phone {phone}")
            return {"error": "Lead not found"}

        lead_id = str(lead.id)

        # Log inbound message
        await self._log_message(lead_id, phone, message, "inbound", button_id)

        if button_id == "interested" or (message and "yes" in message.lower()):
            # Route to payment
            await self.emit_event("stream:payment", lead_id, {
                "name": lead.name,
                "phone": lead.phone,
                "category": lead.category,
                "preview_url": lead.preview_url,
                "source": "whatsapp",
            })
            await self._send_text(
                phone,
                "That's great! 🎉 We'll send you a secure payment link shortly. "
                "Your website will be live within 24 hours of payment!",
                lead_id,
            )
            return {"action": "route_to_payment", "lead_id": lead_id}

        elif button_id == "pricing":
            pricing_message = (
                "📋 *Our Plans:*\n\n"
                "🟢 *Starter* — $49/mo + $99 setup\n"
                "   5-page site, contact form, mobile-ready, SSL\n\n"
                "🔵 *Business* — $99/mo + $149 setup\n"
                "   + Online booking, gallery, reviews widget\n\n"
                "⭐ *Premium* — $199/mo + $249 setup\n"
                "   + Ecommerce, blog, WhatsApp chat widget\n\n"
                "All plans include hosting, SSL, and ongoing updates. "
                "Which plan interests you?"
            )
            await self._send_text(phone, pricing_message, lead_id)
            return {"action": "sent_pricing", "lead_id": lead_id}

        elif button_id == "not_now":
            await self.update_lead_status(lead_id, "NOT_INTERESTED", "Declined via WhatsApp")
            await self._send_text(
                phone,
                "No problem at all! We'll keep your sample site live for 7 days "
                "in case you change your mind. Have a great day! 👋",
                lead_id,
            )
            return {"action": "not_interested", "lead_id": lead_id}

        else:
            # Route to negotiation agent for AI response
            await self.emit_event("stream:negotiate", lead_id, {
                "message": message,
                "channel": "whatsapp",
                "phone": phone,
            })
            return {"action": "route_to_negotiation", "lead_id": lead_id}

    # ── Meta WhatsApp API Helpers ─────────────────────────

    async def _send_text(self, phone: str, body: str, lead_id: str = None):
        """Send a plain text message via WhatsApp API."""
        await self._make_api_call({
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {"body": body},
        })
        if lead_id:
            await self._log_message(lead_id, phone, body, "outbound")

    async def _send_image(self, phone: str, image_url: str, caption: str, lead_id: str = None):
        """Send an image message with caption."""
        await self._make_api_call({
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "image",
            "image": {"link": image_url, "caption": caption},
        })
        if lead_id:
            await self._log_message(lead_id, phone, caption, "outbound", message_type="image", media_url=image_url)

    async def _send_interactive(self, phone: str, body: str, buttons: list[dict], lead_id: str = None):
        """Send an interactive button message."""
        await self._make_api_call({
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {"text": body},
                "action": {
                    "buttons": [
                        {"type": "reply", "reply": {"id": b["id"], "title": b["title"]}}
                        for b in buttons
                    ],
                },
            },
        })
        if lead_id:
            await self._log_message(lead_id, phone, body, "outbound", message_type="interactive")

    async def _make_api_call(self, payload: dict) -> dict:
        """Send a request to the Meta WhatsApp Cloud API."""
        if not settings.WHATSAPP_ACCESS_TOKEN:
            self.logger.warning("WhatsApp API not configured — simulating send")
            return {"status": "simulated"}

        url = f"{self.META_API_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
                    json=payload,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            self.logger.error(f"WhatsApp API error: {e}")
            raise

    async def _log_message(
        self, lead_id: str, phone: str, body: str, direction: str,
        button_id: str = None, message_type: str = "text", media_url: str = None
    ):
        """Save message to database for audit trail."""
        async with self.db() as session:
            msg = WhatsAppMessage(
                lead_id=lead_id,
                phone=phone,
                body=body,
                direction=direction,
                message_type=message_type,
                button_id=button_id,
                media_url=media_url,
            )
            session.add(msg)
            await session.commit()
