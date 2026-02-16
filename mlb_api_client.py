# mlb_api_client.py
import httpx
from cachetools import TTLCache

BASE_URL = "https://statsapi.mlb.com/api/v1"
cache = TTLCache(maxsize=300, ttl=1800)

class MLBClient:
    def __init__(self):
        self.client = None  # Will be set per request

    async def _get(self, endpoint: str, params=None):
        if self.client is None:
            raise Exception("Client not initialized")
        key = f"{endpoint}:{str(sorted((params or {}).items()))}"
        if cached := cache.get(key):
            return cached
        try:
            r = await self.client.get(f"{BASE_URL}{endpoint}", params=params, timeout=10.0)
            r.raise_for_status()
            data = r.json()
            cache[key] = data
            return data
        except Exception as e:
            print("MLB API Error:", e)
            return {}

    async def search_player(self, name: str):
        return await self._get("/people/search", {"name": name, "sportId": 1})

    async def get_player(self, player_id: int):
        return await self._get(f"/people/{player_id}", {
            "hydrate": "team,currentTeam,stats(type=season),injuries,transactions"
        })

    async def get_schedule(self, **kwargs):
        params = {"sportId": 1, "hydrate": "probablePitcher,linescore", **kwargs}
        return await self._get("/schedule", params)

    async def get_leaderboard(self, stat: str, season=None, group="hitting", limit=10):
        params = {"leaderCategories": stat, "statGroup": group, "limit": limit}
        if season == False:  # all-time
            pass
        elif season:
            params["season"] = season
        else:
            params["season"] = "2025"
        return await self._get("/stats/leaders", params)

# Global instance (client will be injected per request)
mlb = MLBClient()
