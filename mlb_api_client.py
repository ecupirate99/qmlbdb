# mlb_api_client.py
import httpx
from cachetools import TTLCache
from datetime import datetime

BASE_URL = "https://statsapi.mlb.com/api/v1"
cache = TTLCache(maxsize=300, ttl=1800)

class MLBClient:
    def __init__(self):
        self.client = httpx.AsyncClient(base_url=BASE_URL, timeout=15.0)

    async def _get(self, endpoint: str, params=None):
        key = f"{endpoint}:{str(sorted((params or {}).items()))}"
        if cached := cache.get(key):
            return cached
        try:
            r = await self.client.get(endpoint, params=params)
            r.raise_for_status()
            data = r.json()
            cache[key] = data
            return data
        except:
            return {}

    async def search_player(self, name: str):
        return await self._get("/people/search", {"name": name, "sportId": 1, "active": True})

    async def get_player(self, player_id: int):
        return await self._get(f"/people/{player_id}", {
            "hydrate": "team,currentTeam,stats(type=season,currentSeason),injuries,transactions"
        })

    async def get_player_stats(self, player_id: int, season=None):
        season = season or datetime.now().year
        return await self._get(f"/people/{player_id}", {
            "hydrate": f"stats(group=[hitting,pitching],type=[season,career,yearByYear],season={season})"
        })

    async def get_schedule(self, **kwargs):
        params = {"sportId": 1, "hydrate": "team,linescore,probablePitcher(note),venue", **kwargs}
        return await self._get("/schedule", params)

    async def get_game_boxscore(self, game_pk: int):
        return await self._get(f"/game/{game_pk}/boxscore")

    async def get_leaderboard(self, stat: str, season=None, group="hitting", limit=10):
        season_str = season or (None if season is False else datetime.now().year)
        params = {
            "leaderCategories": stat,
            "statGroup": group,
            "limit": limit,
            "hydrate": "person,team"
        }
        if season_str:
            params["season"] = season_str
        return await self._get("/stats/leaders", params)

    async def get_all_teams(self, season=None):
        season = season or datetime.now().year
        return await self._get("/teams", {"sportId": 1, "season": season})

# Global instance
mlb = MLBClient()
