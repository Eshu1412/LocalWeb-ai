"""
LocalWeb AI — Negotiation Agent
Handles Q&A and objections using LLM with RAG on a FAQ knowledge base.
"""

import json
from typing import Optional

from openai import AsyncOpenAI

from agents.base_agent import BaseAgent
from config import settings
from prompts.negotiation import NEGOTIATION_PROMPT


class NegotiationAgent(BaseAgent):
    """
    AI-powered objection handling and Q&A agent.

    Pipeline: stream:negotiate → NegotiationAgent → stream:payment (if ready) / WhatsApp reply
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def process(self, lead_id: str, payload: dict) -> dict:
        """
        Process an owner message / objection.

        Steps:
            1. Retrieve relevant FAQ context from vector store (RAG)
            2. Generate personalized response with LLM
            3. Send response via appropriate channel
            4. Classify intent — ready to buy, still objecting, or lost
        """
        message = payload.get("message", "")
        channel = payload.get("channel", "whatsapp")

        self.logger.info(f"Negotiating with lead {lead_id}: {message[:100]}...")
        await self.update_lead_status(lead_id, "NEGOTIATING")

        # 1. RAG — retrieve relevant FAQ context
        faq_context = await self._retrieve_faq_context(message)

        # 2. Get lead info for personalization
        lead = await self.get_lead(lead_id)
        lead_name = lead.name if lead else ""
        lead_category = lead.category if lead else ""

        # 3. Generate response
        response_text = await self._generate_response(
            message=message,
            faq_context=faq_context,
            business_name=lead_name,
            category=lead_category,
        )

        # 4. Send response via same channel
        if channel == "whatsapp" and lead and lead.phone:
            await self._send_whatsapp_reply(lead.phone, response_text, lead_id)
        # For call channel, the response would be converted to speech

        # 5. Classify intent
        intent = await self._classify_intent(message)

        if intent == "ready":
            # Owner is ready to pay — route to Payment Agent
            await self.emit_event("stream:payment", lead_id, {
                "name": lead_name,
                "phone": lead.phone if lead else "",
                "category": lead_category,
                "preview_url": lead.preview_url if lead else "",
                "source": channel,
            })

        return {
            "response": response_text,
            "intent": intent,
            "channel": channel,
        }

    async def _retrieve_faq_context(self, query: str) -> str:
        """
        Retrieve relevant FAQ answers from vector store (Pinecone).
        Falls back to built-in FAQ if Pinecone is not configured.
        """
        if settings.PINECONE_API_KEY:
            try:
                # Pinecone vector search
                from langchain_community.vectorstores import Pinecone as PineconeVS
                from langchain_openai import OpenAIEmbeddings

                embeddings = OpenAIEmbeddings(api_key=settings.OPENAI_API_KEY)
                vectorstore = PineconeVS.from_existing_index(
                    index_name=settings.PINECONE_INDEX_NAME,
                    embedding=embeddings,
                )
                docs = vectorstore.similarity_search(query, k=3)
                return "\n".join([doc.page_content for doc in docs])
            except Exception as e:
                self.logger.warning(f"Pinecone search failed, using built-in FAQ: {e}")

        # Built-in FAQ fallback
        return self._get_builtin_faq()

    def _get_builtin_faq(self) -> str:
        """Built-in FAQ knowledge base for when Pinecone is unavailable."""
        return """
FAQ:
Q: How much does it cost?
A: Our Starter plan is $49/month with a one-time $99 setup fee. We also have Business ($99/mo) and Premium ($199/mo) plans.

Q: How long does it take to build my website?
A: Your website goes live within 24 hours of payment confirmation.

Q: Can I make changes to my website?
A: Yes! You can request changes anytime. Starter includes 2 free revisions/month, Business includes 5, and Premium includes unlimited.

Q: Do I need to know how to code?
A: Not at all! We handle everything — design, content, hosting, and maintenance.

Q: What if I don't like the sample site?
A: We'll customize it to your preferences before going live. The sample is just a starting point.

Q: Can I use my own domain name?
A: Absolutely! We'll set up your custom domain or help you purchase one.

Q: Is there a contract?
A: No long-term contracts. You can cancel anytime. We also offer 2 months free with annual pre-pay.

Q: What's included in the monthly fee?
A: Hosting, SSL certificate, mobile optimization, basic SEO, and monthly backups.
"""

    async def _generate_response(
        self, message: str, faq_context: str,
        business_name: str, category: str
    ) -> str:
        """Generate a personalized response using LLM."""
        system_prompt = NEGOTIATION_PROMPT.format(
            faq_context=faq_context,
            name=business_name,
            category=category,
        )

        try:
            response = await self.openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message},
                ],
                temperature=0.7,
                max_tokens=300,
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"Response generation failed: {e}")
            return (
                "Thanks for your question! Our team will get back to you shortly. "
                "In the meantime, feel free to check out your sample site!"
            )

    async def _classify_intent(self, message: str) -> str:
        """Classify if the owner is ready to buy, still objecting, or not interested."""
        try:
            response = await self.openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Classify the business owner's intent. Reply with ONLY one word: "
                            "ready, objection, or not_interested"
                        ),
                    },
                    {"role": "user", "content": message},
                ],
                temperature=0,
                max_tokens=10,
            )
            intent = response.choices[0].message.content.strip().lower()
            valid = ("ready", "objection", "not_interested")
            return intent if intent in valid else "objection"
        except Exception:
            return "objection"

    async def _send_whatsapp_reply(self, phone: str, body: str, lead_id: str):
        """Send reply via WhatsApp (delegates to WhatsApp agent's API)."""
        import httpx

        if not settings.WHATSAPP_ACCESS_TOKEN:
            self.logger.info(f"Would send WhatsApp to {phone}: {body[:50]}...")
            return

        url = f"https://graph.facebook.com/v18.0/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        async with httpx.AsyncClient(timeout=30) as client:
            await client.post(
                url,
                headers={"Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": phone,
                    "type": "text",
                    "text": {"body": body},
                },
            )
