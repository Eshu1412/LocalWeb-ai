"""
LocalWeb AI — Verification Agent
Checks whether a discovered business already has a website via DNS lookup,
HTTP probing, and Google search. Routes leads accordingly.
"""

import socket

import httpx

from agents.base_agent import BaseAgent
from config import settings


class VerificationAgent(BaseAgent):
    """
    Determines if a business already has a website.

    Pipeline: stream:verify → VerificationAgent → stream:sample_build (if no site)
    """

    async def process(self, lead_id: str, payload: dict) -> dict:
        """
        Check if a business has an existing website.

        Strategy:
            1. Try common domain patterns via DNS + HTTP
            2. Search Google for the business name + location
            3. Mark as HAS_WEBSITE or NO_WEBSITE
        """
        name = payload.get("name", "")
        address = payload.get("address", "")

        await self.update_lead_status(lead_id, "VERIFYING")
        self.logger.info(f"Verifying web presence for: {name}")

        # 1. DNS check — try common domain patterns
        slug = name.lower().replace("'", "").replace("&", "and")
        domains_to_try = [
            f"{slug.replace(' ', '-')}.com",
            f"{slug.replace(' ', '')}.com",
            f"{slug.replace(' ', '')}online.com",
            f"{slug.replace(' ', '-')}.co",
            f"{slug.replace(' ', '')}.net",
        ]

        for domain in domains_to_try:
            result = await self._check_domain(domain)
            if result:
                await self.update_lead_status(lead_id, "HAS_WEBSITE", f"Found: {domain}")
                return {"has_website": True, "url": f"https://{domain}"}

        # 2. Google search for business name + location
        search_result = await self._google_search(name, address)
        if search_result:
            await self.update_lead_status(lead_id, "HAS_WEBSITE", f"Found via search: {search_result}")
            return {"has_website": True, "url": search_result}

        # 3. No website found — proceed to sample builder
        self.logger.info(f"No website found for {name} — routing to Sample Builder")
        await self.update_lead_status(lead_id, "NO_WEBSITE")
        await self.emit_event("stream:sample_build", lead_id, payload)
        return {"has_website": False}

    async def _check_domain(self, domain: str) -> bool:
        """Test if a domain resolves and returns a valid HTTP response."""
        try:
            # DNS lookup (non-blocking via thread)
            import asyncio
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, socket.gethostbyname, domain)

            # HTTP probe
            async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
                response = await client.get(f"https://{domain}")
                if response.status_code < 400:
                    self.logger.info(f"Domain {domain} is live (HTTP {response.status_code})")
                    return True
        except (socket.gaierror, httpx.ConnectError, httpx.TimeoutException):
            pass
        except Exception as e:
            self.logger.debug(f"Domain check failed for {domain}: {e}")
        return False

    async def _google_search(self, name: str, address: str) -> str | None:
        """Search Google via SerpAPI for the business's official website."""
        if not settings.SERPAPI_API_KEY:
            return None

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "q": f"{name} {address} official website",
                        "api_key": settings.SERPAPI_API_KEY,
                        "num": 3,
                    },
                )
                data = response.json()
                results = data.get("organic_results", [])
                if results:
                    # Check if top result looks like an official business site
                    top_url = results[0].get("link", "")
                    # Exclude directories like yelp, yellowpages, facebook
                    skip_domains = ["yelp.com", "yellowpages.com", "facebook.com",
                                    "google.com", "tripadvisor.com", "instagram.com"]
                    if not any(d in top_url for d in skip_domains):
                        return top_url
        except Exception as e:
            self.logger.warning(f"SerpAPI search error: {e}")

        return None
