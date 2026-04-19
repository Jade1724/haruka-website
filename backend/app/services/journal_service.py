import asyncio
import logging
import re
from datetime import date
from time import monotonic

from core.config import settings
from dao.github_dao import GithubDAO
from models.journal import JournalDetail, JournalSummary

logger = logging.getLogger(__name__)

_PATH_RE = re.compile(
    r".*/(?P<year>\d{4})/(?P<mmdd>\d{4})_(?P<slug>[^/]+)\.md$"
)

# Module-level cache shared across all JournalService instances: key -> (value, expiry)
_cache: dict[str, tuple[object, float]] = {}


def _get_cached(key: str) -> object | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    value, expiry = entry
    if monotonic() > expiry:
        del _cache[key]
        return None
    return value


def _set_cached(key: str, value: object) -> None:
    _cache[key] = (value, monotonic() + settings.cache_ttl_seconds)


def _parse_path(path: str) -> tuple[int, int, int, str] | None:
    m = _PATH_RE.match(path)
    if not m:
        return None
    year = int(m.group("year"))
    mmdd = m.group("mmdd")
    return year, int(mmdd[:2]), int(mmdd[2:]), m.group("slug")


def _make_id(year: int, month: int, day: int, slug: str) -> str:
    return f"{year}-{month:02d}-{day:02d}-{slug}"


def _slug_to_title(slug: str) -> str:
    return slug.replace("-", " ").title()


def _extract_title(content: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return ""


class JournalService:
    def __init__(self, dao: GithubDAO) -> None:
        self._dao = dao

    async def _cached_tree(self) -> list[str]:
        cached = _get_cached("tree")
        if cached is not None:
            return cached  # type: ignore[return-value]
        try:
            paths = await self._dao.get_tree()
        except Exception:
            logger.exception("Failed to fetch git tree from GitHub")
            raise
        logger.debug("Fetched git tree: %d paths", len(paths))
        _set_cached("tree", paths)
        return paths

    async def list_journals(self) -> list[JournalSummary]:
        cached = _get_cached("list")
        if cached is not None:
            return cached  # type: ignore[return-value]

        try:
            paths = await self._cached_tree()
        except Exception:
            logger.exception("list_journals: could not retrieve tree")
            raise

        valid = [(path, parsed) for path in paths if (parsed := _parse_path(path))]
        logger.debug("list_journals: %d valid journal paths found", len(valid))

        try:
            commit_dates = await asyncio.gather(
                *(self._dao.get_last_commit_date(path) for path, _ in valid)
            )
        except Exception:
            logger.exception("list_journals: failed to fetch commit dates")
            raise

        summaries: list[JournalSummary] = [
            JournalSummary(
                id=_make_id(*parsed),
                title=_slug_to_title(parsed[3]),
                published_on=date(parsed[0], parsed[1], parsed[2]),
                updated_on=updated_on,
            )
            for (_, parsed), updated_on in zip(valid, commit_dates)
        ]

        summaries.sort(key=lambda s: s.published_on, reverse=True)
        _set_cached("list", summaries)
        logger.debug("list_journals: returning %d summaries", len(summaries))
        return summaries

    async def get_journal(self, journal_id: str) -> JournalDetail | None:
        cached = _get_cached(journal_id)
        if cached is not None:
            return cached  # type: ignore[return-value]

        try:
            paths = await self._cached_tree()
        except Exception:
            logger.exception("get_journal(%s): could not retrieve tree", journal_id)
            raise

        target_path: str | None = None
        target_parsed: tuple[int, int, int, str] | None = None

        for path in paths:
            parsed = _parse_path(path)
            if parsed and _make_id(*parsed) == journal_id:
                target_path = path
                target_parsed = parsed
                break

        if target_path is None or target_parsed is None:
            logger.warning("get_journal(%s): no matching path found in tree", journal_id)
            return None

        logger.debug("get_journal(%s): fetching content from %s", journal_id, target_path)

        try:
            content, updated_on = await asyncio.gather(
                self._dao.get_file_content(target_path),
                self._dao.get_last_commit_date(target_path),
            )
        except Exception:
            logger.exception(
                "get_journal(%s): failed to fetch content or commit date for %s",
                journal_id,
                target_path,
            )
            raise

        year, month, day, slug = target_parsed
        detail = JournalDetail(
            id=journal_id,
            title=_extract_title(content) or _slug_to_title(slug),
            published_on=date(year, month, day),
            updated_on=updated_on,
            content=content,
        )
        _set_cached(journal_id, detail)
        return detail
