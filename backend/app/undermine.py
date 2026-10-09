import httpx
import logging
from typing import Optional, Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)

class UndermineClient:
    BASE_URL = "https://api.undermine.exchange"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.UNDERMINE_API_KEY
        self.headers = {
            "Accept-Encoding": "gzip",
            "User-Agent": "WoWMidnightMarketTracker/1.0"
        }
        if self.api_key:
            self.headers["Authorization"] = f"ApiKey {self.api_key}"

    async def get_commodities(self, region: str) -> Optional[Dict[str, Any]]:
        """Fetch region-wide commodity data."""
        url = f"{self.BASE_URL}/v1/region/{region.lower()}/commodities.json"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 403:
                    logger.error("Undermine API Forbidden (403): Verify API Key.")
                else:
                    logger.warning(f"Undermine API response error: {resp.status_code}")
                return None
            except httpx.RequestError as exc:
                logger.error(f"HTTP error during commodity fetch: {exc}")
                return None

    async def get_item_history(self, region: str, item_id: int) -> Optional[List[Dict[str, Any]]]:
        """Fetch historical commodity data if available."""
        url = f"{self.BASE_URL}/v1/region/{region.lower()}/item/{item_id}.json"
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("history", [])
                return None
            except Exception as e:
                logger.error(f"Failed to fetch item history {item_id}: {e}")
                return None
