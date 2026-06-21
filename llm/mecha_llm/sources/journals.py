"""Pull dev-journal markdown from the private Obsidian GitHub repo.

Mirrors ``backend/app/dao/github_dao.py`` and the ID/route scheme in
``backend/app/services/journal_service.py`` (path ``.../YYYY/MMDD_slug.md`` →
id ``YYYY-MM-DD-slug`` → route ``/journal/{id}``) so chatbot citations link to the
same pages the site serves.
"""

from __future__ import annotations

import asyncio
import base64
import re

import aiohttp

from ..config import settings
from ..documents import SourceDoc

_BASE_URL = "https://api.github.com"
_PATH_RE = re.compile(r".*/(?P<year>\d{4})/(?P<mmdd>\d{4})_(?P<slug>[^/]+)\.md$")


def _headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {settings.github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _parse_path(path: str) -> tuple[int, int, int, str] | None:
    m = _PATH_RE.match(path)
    if not m:
        return None
    mmdd = m.group("mmdd")
    return int(m.group("year")), int(mmdd[:2]), int(mmdd[2:]), m.group("slug")


def _make_id(year: int, month: int, day: int, slug: str) -> str:
    return f"{year}-{month:02d}-{day:02d}-{slug}"


def _extract_title(content: str, slug: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return slug.replace("-", " ").title()


async def _get_json(session: aiohttp.ClientSession, url: str, params: dict | None = None):
    async with session.get(url, headers=_headers(), params=params) as resp:
        resp.raise_for_status()
        return await resp.json()


async def _get_tree(session: aiohttp.ClientSession) -> list[str]:
    url = f"{_BASE_URL}/repos/{settings.github_repo}/git/trees/HEAD"
    data = await _get_json(session, url, params={"recursive": "1"})
    return [
        item["path"]
        for item in data["tree"]
        if item["type"] == "blob"
        and item["path"].startswith(settings.journals_base_path)
        and item["path"].endswith(".md")
    ]


async def _get_content(session: aiohttp.ClientSession, path: str) -> str:
    url = f"{_BASE_URL}/repos/{settings.github_repo}/contents/{path}"
    data = await _get_json(session, url)
    return base64.b64decode(data["content"].replace("\n", "")).decode("utf-8")


async def fetch_journal_docs() -> list[SourceDoc]:
    """Fetch every journal entry as a ``SourceDoc``. Requires ``github_token``."""
    settings.require("github_token")

    connector = aiohttp.TCPConnector(limit=20)
    async with aiohttp.ClientSession(connector=connector) as session:
        paths = await _get_tree(session)
        valid = [(p, parsed) for p in paths if (parsed := _parse_path(p))]
        contents = await asyncio.gather(*(_get_content(session, p) for p, _ in valid))

    docs: list[SourceDoc] = []
    for (_, parsed), content in zip(valid, contents):
        year, month, day, slug = parsed
        journal_id = _make_id(year, month, day, slug)
        docs.append(
            SourceDoc(
                doc_id=f"journal-{journal_id}",
                title=_extract_title(content, slug),
                text=content,
                source_type="journal",
                url=f"/journal/{journal_id}",
                published_on=f"{year:04d}-{month:02d}-{day:02d}",
            )
        )
    return docs
