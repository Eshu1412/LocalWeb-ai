"""
LocalWeb AI — Discovery Agent
Finds local businesses by area and category using Google Places API + Yelp.
Deduplicates results, saves to PostgreSQL, and emits to the verification stream.
"""

import asyncio
import uuid
from typing import Optional

import httpx

from agents.base_agent import BaseAgent
from config import settings
from db.models import BusinessLead


class DiscoveryAgent(BaseAgent):
    """
    Discovers local businesses without websites.

    Pipeline: Orchestrator → DiscoveryAgent → stream:verify
    """

    async def process(self, lead_id: str, payload: dict) -> dict:
        """
        Discover businesses for a given area and category.

        Args:
            payload: {"area": "Brooklyn, NY", "category": "restaurant"}
        """
        area = payload.get("area", "")
        category = payload.get("category", "")

        if not area or not category:
            self.logger.error("Missing area or category in discovery payload")
            return {"error": "Missing area or category"}

        self.logger.info(f"Discovering {category} businesses in {area}")

        # 1. Query Google Places API
        google_leads = await self._search_google_places(area, category)

        # 2. Query Yelp as backup source
        yelp_leads = await self._search_yelp(area, category)

        # 3. Merge and deduplicate
        all_leads = self._deduplicate(google_leads + yelp_leads)
        self.logger.info(f"Found {len(all_leads)} unique leads for {category} in {area}")

        # 4. Save to database and emit to verification
        saved_count = 0
        for lead_data in all_leads:
            try:
                lead = await self._save_lead(lead_data)
                if lead:
                    await self.emit_event("stream:verify", str(lead.id), {
                        "name": lead.name,
                        "phone": lead.phone,
                        "address": lead.address,
                        "category": lead.category,
                        "area": lead.area,
                        "place_id": lead.place_id,
                    })
                    saved_count += 1
            except Exception as e:
                self.logger.error(f"Failed to save lead {lead_data.get('name')}: {e}")

        return {
            "area": area,
            "category": category,
            "google_results": len(google_leads),
            "yelp_results": len(yelp_leads),
            "unique_leads": len(all_leads),
            "saved": saved_count,
        }

    async def _search_google_places(self, area: str, category: str) -> list[dict]:
        """Query Google Places API Text Search endpoint with pagination."""
        if not settings.GOOGLE_PLACES_API_KEY:
            self.logger.warning("GOOGLE_PLACES_API_KEY not set, skipping Google search")
            return []

        leads = []
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": f"{category} in {area}",
            "key": settings.GOOGLE_PLACES_API_KEY,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            for page in range(3):  # Max 3 pages (60 results)
                try:
                    response = await self.retry_with_backoff(
                        client.get, url, params=params
                    )
                    data = response.json()

                    for place in data.get("results", []):
                        lead = {
                            "name": place.get("name", ""),
                            "address": place.get("formatted_address", ""),
                            "category": category,
                            "area": area,
                            "place_id": place.get("place_id", ""),
                            "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                            "lng": place.get("geometry", {}).get("location", {}).get("lng"),
                            "source": "google_places",
                        }
                        # Get phone via Place Details
                        if place.get("place_id"):
                            details = await self._get_place_details(
                                client, place["place_id"]
                            )
                            lead["phone"] = details.get("formatted_phone_number")
                            lead["website"] = details.get("website")

                        leads.append(lead)

                    # Check for next page
                    next_token = data.get("next_page_token")
                    if not next_token:
                        break
                    params["pagetoken"] = next_token
                    await asyncio.sleep(2)  # Google requires delay between pages

                except Exception as e:
                    self.logger.error(f"Google Places API error on page {page}: {e}")
                    break

        return leads

    async def _get_place_details(self, client: httpx.AsyncClient, place_id: str) -> dict:
        """Fetch detailed info for a single place."""
        url = "https://maps.googleapis.com/maps/api/place/details/json"
        params = {
            "place_id": place_id,
            "fields": "formatted_phone_number,website",
            "key": settings.GOOGLE_PLACES_API_KEY,
        }
        try:
            response = await client.get(url, params=params, timeout=10)
            return response.json().get("result", {})
        except Exception as e:
            self.logger.warning(f"Place details fetch failed for {place_id}: {e}")
            return {}

    async def _search_yelp(self, area: str, category: str) -> list[dict]:
        """Query Yelp Fusion API as a backup discovery source."""
        if not settings.SERPAPI_API_KEY:
            return []

        leads = []
        url = "https://api.yelp.com/v3/businesses/search"
        headers = {"Authorization": f"Bearer {settings.SERPAPI_API_KEY}"}
        params = {
            "term": category,
            "location": area,
            "limit": 50,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await self.retry_with_backoff(
                    client.get, url, headers=headers, params=params
                )
                data = response.json()
                for biz in data.get("businesses", []):
                    leads.append({
                        "name": biz.get("name", ""),
                        "phone": biz.get("phone", ""),
                        "address": ", ".join(biz.get("location", {}).get("display_address", [])),
                        "category": category,
                        "area": area,
                        "place_id": f"yelp:{biz.get('id', '')}",
                        "lat": biz.get("coordinates", {}).get("latitude"),
                        "lng": biz.get("coordinates", {}).get("longitude"),
                        "source": "yelp",
                    })
            except Exception as e:
                self.logger.error(f"Yelp API error: {e}")

        return leads

    def _deduplicate(self, leads: list[dict]) -> list[dict]:
        """Remove duplicate leads by phone number and place_id."""
        seen_phones = set()
        seen_place_ids = set()
        unique = []

        for lead in leads:
            phone = lead.get("phone", "")
            pid = lead.get("place_id", "")

            if phone and phone in seen_phones:
                continue
            if pid and pid in seen_place_ids:
                continue

            if phone:
                seen_phones.add(phone)
            if pid:
                seen_place_ids.add(pid)
            unique.append(lead)

        return unique

    async def _save_lead(self, lead_data: dict) -> Optional[BusinessLead]:
        """Save a new lead to PostgreSQL if it doesn't already exist."""
        from sqlalchemy import select

        async with self.db() as session:
            # Check for existing lead by place_id
            if lead_data.get("place_id"):
                existing = await session.execute(
                    select(BusinessLead).where(
                        BusinessLead.place_id == lead_data["place_id"]
                    )
                )
                if existing.scalar_one_or_none():
                    return None

            lead = BusinessLead(
                id=uuid.uuid4(),
                name=lead_data["name"],
                phone=lead_data.get("phone"),
                address=lead_data.get("address"),
                category=lead_data["category"],
                area=lead_data["area"],
                place_id=lead_data.get("place_id"),
                lat=lead_data.get("lat"),
                lng=lead_data.get("lng"),
                source=lead_data.get("source", "google_places"),
                status="DISCOVERED",
            )
            session.add(lead)
            await session.commit()
            await session.refresh(lead)
            return lead
