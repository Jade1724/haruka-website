"""Content sources for the mecha-haruka knowledge base.

Each module exposes a function returning a list of ``SourceDoc``. ``collect_all_docs``
aggregates them. Journals are fetched over the network (async); projects, experience,
and site routes are local/static.
"""

from __future__ import annotations

from ..config import settings
from ..documents import SourceDoc
from .content_json import load_content_docs
from .journals import fetch_journal_docs
from .routes import route_docs

__all__ = [
    "load_content_docs",
    "fetch_journal_docs",
    "route_docs",
    "collect_all_docs",
]


async def collect_all_docs() -> list[SourceDoc]:
    """Gather documents from every source. Requires ``github_token`` for journals."""
    docs: list[SourceDoc] = []
    docs.extend(route_docs())
    docs.extend(load_content_docs(settings.content_json_path))
    docs.extend(await fetch_journal_docs())
    return docs
