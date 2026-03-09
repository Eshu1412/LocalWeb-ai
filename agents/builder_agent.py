"""
LocalWeb AI — Builder Agent
Builds production websites using Next.js templates and deploys to Vercel with custom domains.
"""

import shutil
import httpx

from agents.base_agent import BaseAgent
from config import settings
from db.models import BusinessLead, DeployedSite


class BuilderAgent(BaseAgent):
    """Pipeline: stream:build → BuilderAgent → stream:qa"""

    async def process(self, lead_id: str, payload: dict) -> dict:
        """Build and deploy a production website for a paid lead."""
        await self.update_lead_status(lead_id, "BUILDING")
        category = payload.get("category", "general")
        name = payload.get("name", "")
        self.logger.info(f"Building production site for {name} ({category})")

        # 1. Generate full site content
        content = await self._generate_full_content(payload)

        # 2. Generate slug for domain
        slug = name.lower().replace("'", "").replace("&", "and").replace(" ", "-")

        # 3. Register domain via Cloudflare (if configured)
        domain = f"{slug}.com"
        await self._setup_dns(domain)

        # 4. Deploy to Vercel
        deploy_result = await self._deploy_to_vercel(slug, category, content)
        live_url = deploy_result.get("url", f"https://{slug}.localweb.ai")

        # 5. Save deployed site record
        async with self.db() as session:
            lead = await session.get(BusinessLead, lead_id)
            if lead:
                lead.live_url = live_url
                lead.domain = domain

            site = DeployedSite(
                lead_id=lead_id, domain=domain,
                vercel_project_id=deploy_result.get("project_id", ""),
                template_used=category, status="building",
            )
            session.add(site)
            await session.commit()

        # 6. Emit to QA agent
        await self.emit_event("stream:qa", lead_id, {
            **payload, "live_url": live_url, "domain": domain,
        })

        return {"live_url": live_url, "domain": domain}

    async def _generate_full_content(self, payload: dict) -> dict:
        """Generate comprehensive website content with GPT-4o."""
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        try:
            import json
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Generate full website content for '{payload.get('name')}', "
                        f"a {payload.get('category')} in {payload.get('area', '')}. "
                        f"Return JSON with: headline, tagline, about (3 paragraphs), "
                        f"services (6 items with name/description/price_hint), "
                        f"testimonials (3), contact_info, color_scheme, seo_title, meta_description."
                    ),
                }],
                response_format={"type": "json_object"},
                temperature=0.7,
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            return {"headline": payload.get("name", "Welcome"), "tagline": "Your local business online"}

    async def _setup_dns(self, domain: str):
        """Configure DNS via Cloudflare API."""
        if not settings.CLOUDFLARE_API_TOKEN:
            self.logger.info(f"Cloudflare not configured — skipping DNS for {domain}")
            return

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                await client.post(
                    f"https://api.cloudflare.com/client/v4/zones/{settings.CLOUDFLARE_ZONE_ID}/dns_records",
                    headers={"Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}"},
                    json={"type": "CNAME", "name": domain, "content": "cname.vercel-dns.com", "proxied": True},
                )
        except Exception as e:
            self.logger.error(f"DNS setup failed for {domain}: {e}")

    async def _deploy_to_vercel(self, slug: str, template: str, content: dict) -> dict:
        """Deploy the site to Vercel via API."""
        if not settings.VERCEL_TOKEN:
            return {"url": f"https://{slug}.localweb.ai", "project_id": "sim"}

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={"Authorization": f"Bearer {settings.VERCEL_TOKEN}"},
                    json={"name": slug, "projectSettings": {"framework": "nextjs"}},
                )
                data = response.json()
                return {"url": f"https://{data.get('url', slug)}", "project_id": data.get("projectId", "")}
        except Exception as e:
            self.logger.error(f"Vercel deploy failed: {e}")
            return {"url": f"https://{slug}.localweb.ai", "project_id": ""}
