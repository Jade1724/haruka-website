import base64
from datetime import date, datetime

import aiohttp

from core.config import settings


class GithubDAO:
    _BASE_URL = "https://api.github.com"

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings.github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    async def _get(self, url: str, params: dict | None = None) -> dict | list:
        async with self._session.get(url, headers=self._headers(), params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get_tree(self) -> list[str]:
        """Return all .md blob paths under journals_base_path via a single recursive tree call."""
        url = f"{self._BASE_URL}/repos/{settings.github_repo}/git/trees/HEAD"
        data = await self._get(url, params={"recursive": "1"})
        return [
            item["path"]
            for item in data["tree"]
            if item["type"] == "blob"
            and item["path"].startswith(settings.journals_base_path)
            and item["path"].endswith(".md")
        ]

    async def get_file_content(self, path: str) -> str:
        """Return decoded UTF-8 content of a file via the Contents API."""
        url = f"{self._BASE_URL}/repos/{settings.github_repo}/contents/{path}"
        data = await self._get(url)
        raw_b64 = data["content"].replace("\n", "")
        return base64.b64decode(raw_b64).decode("utf-8")

    async def get_last_commit_date(self, path: str) -> date:
        """Return the date of the most recent commit touching this path."""
        url = f"{self._BASE_URL}/repos/{settings.github_repo}/commits"
        data = await self._get(url, params={"path": path, "per_page": "1"})
        if not data:
            return date.today()
        iso_str = data[0]["commit"]["committer"]["date"]
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00")).date()
