import base64
import hashlib
import hmac
import time
import urllib.parse

import httpx

from douban_scraper.ratelimit import RateLimiter, handle_api_error, RetryDecision

API_KEY = "0dad551ec0f84ed02907ff5c42e8ec70"
HMAC_SECRET = b"bf7dddc7c9cfe6f7"
DEFAULT_USER_AGENT = (
    "api-client/1 com.douban.frodo/7.22.0.beta9(231) Android/23"
    " product/Mate40 vendor/HUAWEI model/Mate40 brand/HUAWEI"
    " rom/android network/wifi platform/AndroidPad"
)


def compute_signature(url_path: str, timestamp: str) -> str:
    """Compute HMAC-SHA1 signature for Douban Frodo API request."""
    encoded_path = urllib.parse.quote(url_path, safe="")
    raw_string = "GET&" + encoded_path + "&" + timestamp
    sig = hmac.new(HMAC_SECRET, raw_string.encode(), hashlib.sha1)
    return base64.b64encode(sig.digest()).decode()


class DoubanFrodoClient:
    """Client for Douban's Frodo mobile API (movies, books, music interests)."""

    def __init__(
        self,
        api_key: str = API_KEY,
        api_secret: bytes = HMAC_SECRET,
        user_agent: str = DEFAULT_USER_AGENT,
        base_url: str = "https://frodo.douban.com",
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.user_agent = user_agent
        self.base_url = base_url
        self._last_request_time = 0.0
        self._delay = 1.5
        self._rate_limiter = RateLimiter(delay=1.5)
        self.failures: list[dict] = []

    def _enforce_rate_limit(self) -> None:
        self._rate_limiter.wait()

    def _make_request(self, url: str, params: dict) -> httpx.Response:
        backoff_times = [5, 10, 20]
        last_exc: Exception | None = None
        for attempt in range(4):
            self._enforce_rate_limit()
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.get(
                        url,
                        params=params,
                        headers={
                            "User-Agent": self.user_agent,
                            "Accept": "application/json",
                        },
                    )
                self._last_request_time = time.monotonic()
                data = resp.json()
                code = data.get("code", 0)
                if code != 0:
                    decision = handle_api_error(code)
                    if decision == RetryDecision.FATAL:
                        raise RuntimeError(f"API error {code}: {data.get('msg', 'unknown')}")
                    if attempt < 3:
                        time.sleep(backoff_times[attempt])
                        continue
                    raise RuntimeError(f"API error {code} persisted after retries")
                return resp
            except RuntimeError:
                raise
            except Exception as exc:
                last_exc = exc
                if attempt < 3:
                    time.sleep(backoff_times[attempt])
                    continue
                raise
        raise last_exc  # type: ignore[misc]

    def get_interests(
        self,
        user_id: str,
        type_: str,
        status: str,
        start: int = 0,
        count: int = 50,
    ) -> "FrodoInterestsResponse":
        """Fetch a page of interests for a user."""
        from douban_scraper.models import FrodoInterestsResponse

        url_path = f"/api/v2/user/{user_id}/interests"
        url = f"{self.base_url}{url_path}"
        ts = str(int(time.time()))
        sig = compute_signature(url_path, ts)
        params = {
            "type": type_,
            "status": status,
            "start": str(start),
            "count": str(count),
            "apiKey": self.api_key,
            "_ts": ts,
            "_sig": sig,
            "os_rom": "android",
        }
        resp = self._make_request(url, params)
        return FrodoInterestsResponse.model_validate(resp.json())

    def validate_user(self, user_id: str) -> bool:
        """Check if a Douban user ID is valid by fetching their interests."""
        try:
            resp = self.get_interests(user_id, "movie", "done", start=0, count=1)
            return resp.total >= 0
        except Exception as exc:
            import sys
            print(f"Warning: validate_user failed for {user_id}: {exc}", file=sys.stderr)
            return False

    def export_all(
        self,
        user_id: str,
        type_: str,
        status: str,
        progress_callback=None,
        max_items: int = 0,
        start_offset: int = 0,
    ) -> list[dict]:
        """Export all interests with pagination, retry, and optional max_items."""
        all_interests: list = []
        offset = start_offset
        total = None
        while True:
            resp = self.get_interests(user_id, type_, status, start=offset, count=50)
            if total is None:
                total = resp.total
            interests = resp.interests
            if not interests:
                break
            all_interests.extend(interests)
            offset += len(interests)
            if progress_callback is not None:
                progress_callback(type_, status, offset, total)
            if total is not None and len(all_interests) >= total:
                break
            if max_items > 0 and len(all_interests) >= max_items:
                break
        return [item.model_dump() for item in all_interests]
