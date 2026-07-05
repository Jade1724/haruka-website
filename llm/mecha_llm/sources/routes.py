"""Navigation documents — one per site route.

These let the chatbot answer "which page should I look at?" by retrieving a route
to suggest. Hand-authored so they describe what each page is for; kept short.
"""

from __future__ import annotations

from ..documents import SourceDoc

_ROUTES: list[dict] = [
    {
        "title": "Projects",
        "url": "/",
        "text": (
            "The Projects page is the site home. It showcases Haruka's software "
            "projects — personal, commercial, and research — each with a description, "
            "screenshots, and links to public GitHub repositories where available. "
            "Go here to browse what Haruka has built."
        ),
    },
    {
        "title": "Experience",
        "url": "/experience",
        "text": (
            "The Experience page lists Haruka's career timeline: work history "
            "(roles, employers, dates) and education (degrees and university). "
            "Go here for Haruka's professional background and qualifications."
        ),
    },
    {
        "title": "Journal",
        "url": "/journal",
        "text": (
            "The Journal page is Haruka's dev journal — entries written while building "
            "projects, covering tools, techniques, and lessons learned. Each entry has "
            "its own page at /journal/{id}. Go here to read Haruka's engineering write-ups."
        ),
    },
]


def route_docs() -> list[SourceDoc]:
    return [
        SourceDoc(
            doc_id=f"page-{r['url'].strip('/') or 'home'}",
            title=r["title"],
            text=r["text"],
            source_type="page",
            url=r["url"],
        )
        for r in _ROUTES
    ]
