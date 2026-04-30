import time

import httpx

from douban_scraper.models import RexxBroadcastsResponse
from douban_scraper.ratelimit import RateLimiter


class DoubanRexxarClient:
    """Client for Douban's Rexxar API (broadcasts/statuses)."""

    def __init__(
        self,
        ck_cookie: str = "",
        base_url: str = "https://m.douban.com",
    ):
        self.ck_cookie = ck_cookie
        self.base_url = base_url
        self._rate_limiter = RateLimiter(delay=1.5)

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Referer": "https://m.douban.com/",
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            ),
        }
        if self.ck_cookie:
            headers["Cookie"] = f"ck={self.ck_cookie}"
        return headers

    def get_broadcasts(
        self,
        user_id: str,
        start: int = 0,
        count: int = 20,
    ) -> RexxBroadcastsResponse:
        """Fetch a page of broadcasts for a user."""
        url = f"{self.base_url}/rexxar/api/v2/status/user_timeline/{user_id}"
        params = {"start": start, "count": count}

        self._rate_limiter.wait()
        with httpx.Client(headers=self._build_headers(), timeout=30) as client:
            resp = client.get(url, params=params)

        if resp.status_code in (401, 403):
            raise RuntimeError(
                "Cookie expired or invalid "
                f"(HTTP {resp.status_code}). "
                "Please provide a fresh ck cookie."
            )
        resp.raise_for_status()

        data = resp.json()
        return RexxBroadcastsResponse.model_validate(data)

    def export_all(
        self,
        user_id: str,
        max_items: int = 0,
    ) -> list[dict]:
        """Export all broadcasts with pagination."""
        if not self.ck_cookie:
            print("Warning: No cookie provided. Cannot fetch Rexxar data.")
            return []

        all_broadcasts = []
        start = 0
        count = 20

        while True:
            response = self.get_broadcasts(user_id, start=start, count=count)
            items = response.items

            if not items:
                break

            all_broadcasts.extend(items)

            if 0 < max_items <= len(all_broadcasts):
                all_broadcasts = all_broadcasts[:max_items]
                break

            start += len(items)
            time.sleep(1.5)

        return [item.model_dump() for item in all_broadcasts]
