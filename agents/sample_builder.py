"""
LocalWeb AI — Sample Builder Agent
Generates a personalized website preview for a business using GPT-4o
content generation + template rendering + Vercel deployment.
"""

import json

import httpx
from openai import AsyncOpenAI

from agents.base_agent import BaseAgent
from config import settings
from prompts.sample_builder import SAMPLE_BUILDER_PROMPT


class SampleBuilderAgent(BaseAgent):
    """
    Creates a preview website tailored to the business.

    Pipeline: stream:sample_build → SampleBuilderAgent → stream:outreach
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    async def process(self, lead_id: str, payload: dict) -> dict:
        """
        Generate a sample website:
            1. Generate content with GPT-4o
            2. Select and render template
            3. Deploy to preview subdomain
            4. Take screenshot for outreach
        """
        await self.update_lead_status(lead_id, "SAMPLE_BUILDING")
        self.logger.info(f"Building sample site for: {payload.get('name')}")

        # 1. Generate website content with GPT-4o
        content = await self._generate_content(payload)

        # 2. Select template based on category
        template_name = self._select_template(payload.get("category", "general"))

        # 3. Build and deploy preview site
        preview_url = await self._deploy_preview(lead_id, template_name, content)

        # 4. Capture screenshot for WhatsApp/email preview
        screenshot_url = await self._capture_screenshot(preview_url)

        # 5. Update lead and emit to outreach stream
        async with self.db() as session:
            lead = await session.get(
                __import__("db.models", fromlist=["BusinessLead"]).BusinessLead,
                lead_id,
            )
            if lead:
                lead.preview_url = preview_url
                await session.commit()

        await self.update_lead_status(lead_id, "SAMPLE_READY")
        await self.emit_event("stream:outreach", lead_id, {
            **payload,
            "preview_url": preview_url,
            "screenshot_url": screenshot_url,
            "content": content,
        })

        return {
            "preview_url": preview_url,
            "screenshot_url": screenshot_url,
            "template": template_name,
        }

    async def _generate_content(self, payload: dict) -> dict:
        """Use GPT-4o to generate website content from the business data."""
        prompt = SAMPLE_BUILDER_PROMPT.format(
            name=payload.get("name", ""),
            address=payload.get("address", ""),
            category=payload.get("category", ""),
            google_data=json.dumps(payload.get("extra_data", {})),
        )

        try:
            response = await self.openai.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert web copywriter for local businesses. Return ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=1500,
            )
            content = json.loads(response.choices[0].message.content)
            self.logger.info(f"Generated content: {content.get('headline', 'N/A')}")
            return content
        except Exception as e:
            self.logger.error(f"Content generation failed: {e}")
            # Fallback content
            return {
                "headline": f"Welcome to {payload.get('name', 'Our Business')}",
                "tagline": f"Your trusted {payload.get('category', 'local')} service",
                "about": f"{payload.get('name')} serves the {payload.get('area', 'local')} community with dedication and quality.",
                "services": [{"name": "Our Services", "description": "Quality services for you"}],
                "cta_text": "Contact Us Today",
                "color_scheme": {"primary": "#2563EB", "secondary": "#1E40AF", "accent": "#F59E0B"},
            }

    def _select_template(self, category: str) -> str:
        """Map business category to a website template."""
        template_map = {
            "restaurant": "restaurant",
            "cafe": "restaurant",
            "bakery": "restaurant",
            "salon": "salon",
            "barbershop": "salon",
            "spa": "salon",
            "clinic": "clinic",
            "dentist": "clinic",
            "doctor": "clinic",
            "gym": "gym",
            "fitness": "gym",
            "auto repair": "auto_repair",
            "mechanic": "auto_repair",
            "plumber": "service_provider",
            "electrician": "service_provider",
            "pet store": "retail",
            "pharmacy": "retail",
            "florist": "retail",
            "laundry": "service_provider",
        }
        return template_map.get(category.lower(), "general")

    async def _deploy_preview(self, lead_id: str, template: str, content: dict) -> str:
        """Deploy the preview site to Vercel via API."""
        if not settings.VERCEL_TOKEN:
            self.logger.warning("VERCEL_TOKEN not set — using placeholder URL")
            return f"https://preview-{str(lead_id)[:8]}.localweb.ai"

        subdomain = f"preview-{str(lead_id)[:8]}"
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Create Vercel project and deploy
                response = await client.post(
                    "https://api.vercel.com/v13/deployments",
                    headers={
                        "Authorization": f"Bearer {settings.VERCEL_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "name": subdomain,
                        "files": self._generate_site_files(template, content),
                        "projectSettings": {
                            "framework": "nextjs",
                        },
                    },
                )
                data = response.json()
                url = data.get("url", subdomain)
                return f"https://{url}"
        except Exception as e:
            self.logger.error(f"Vercel deployment failed: {e}")
            return f"https://preview-{str(lead_id)[:8]}.localweb.ai"

    def _generate_site_files(self, template: str, content: dict) -> list[dict]:
        """Generate the file list for Vercel deployment."""
        index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{content.get('seo_title', content.get('headline', 'Welcome'))}</title>
    <meta name="description" content="{content.get('meta_description', '')}">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: 'Inter', system-ui, sans-serif; color: #1a1a1a; }}
        .hero {{ background: linear-gradient(135deg, {content.get('color_scheme', {}).get('primary', '#2563EB')}, {content.get('color_scheme', {}).get('secondary', '#1E40AF')}); color: white; padding: 100px 20px; text-align: center; }}
        .hero h1 {{ font-size: 3rem; margin-bottom: 16px; }}
        .hero p {{ font-size: 1.3rem; opacity: 0.9; }}
        .cta {{ display: inline-block; margin-top: 30px; padding: 16px 40px; background: {content.get('color_scheme', {}).get('accent', '#F59E0B')}; color: #111; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 1.1rem; }}
        .section {{ padding: 80px 20px; max-width: 900px; margin: 0 auto; }}
        .services {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 24px; }}
        .service-card {{ padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>{content.get('headline', 'Welcome')}</h1>
        <p>{content.get('tagline', '')}</p>
        <a href="#contact" class="cta">{content.get('cta_text', 'Get Started')}</a>
    </div>
    <div class="section">
        <h2>About Us</h2>
        <p>{content.get('about', '')}</p>
    </div>
    <div class="section">
        <h2>Our Services</h2>
        <div class="services">
            {''.join(f'<div class="service-card"><h3>{s.get("name", "")}</h3><p>{s.get("description", "")}</p></div>' for s in content.get('services', []))}
        </div>
    </div>
</body>
</html>"""
        return [{"file": "index.html", "data": index_html}]

    async def _capture_screenshot(self, url: str) -> str:
        """Take a screenshot of the preview site for WhatsApp preview."""
        # In production, use Playwright to capture; return placeholder for now
        self.logger.info(f"Would capture screenshot of {url}")
        return f"{url}/screenshot.png"
