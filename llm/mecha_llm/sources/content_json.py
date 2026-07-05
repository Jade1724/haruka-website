"""Load projects + experience from the frontend's content file.

Reads ``frontend/lib/content.json`` (the same file that renders the Projects and
Experience pages) so the chatbot's knowledge stays in sync with the site. Projects
cite the Projects page (``/``) plus any public repo link; experience cites
``/experience``.
"""

from __future__ import annotations

import json
from pathlib import Path

from ..documents import SourceDoc


def _first_github_link(links: list[dict]) -> str | None:
    for link in links:
        if link.get("type") == "github" and link.get("url"):
            return link["url"]
    return None


def _project_doc(project: dict) -> SourceDoc:
    title = project["title"]
    repo_url = _first_github_link(project.get("links", []))
    parts = [
        title,
        f"Type: {project.get('projectType', '')}".strip(),
        project.get("description", ""),
    ]
    if repo_url:
        parts.append(f"Public repository: {repo_url}")
    text = "\n\n".join(p for p in parts if p)
    return SourceDoc(
        doc_id=f"project-{_slugify(title)}",
        title=title,
        text=text,
        source_type="project",
        url="/",
        repo_url=repo_url,
    )


def _experience_doc(entry: dict, kind: str) -> SourceDoc:
    title = entry["title"]
    org = entry.get("organisation", {}).get("name", "")
    start = entry.get("startYear")
    end = entry.get("endYear") or "Present"
    period = f"{start}–{end}" if start else ""
    header = " at ".join(p for p in (title, org) if p)
    parts = [
        header,
        f"{kind.capitalize()} · {period}".strip(" ·"),
        entry.get("description", ""),
    ]
    text = "\n\n".join(p for p in parts if p)
    return SourceDoc(
        doc_id=f"{kind}-{_slugify(title)}-{_slugify(org)}",
        title=header,
        text=text,
        source_type="experience",
        url="/experience",
    )


def _slugify(value: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in value.lower()).strip("-")


def load_content_docs(content_json_path: str | Path) -> list[SourceDoc]:
    path = Path(content_json_path)
    data = json.loads(path.read_text(encoding="utf-8"))

    docs: list[SourceDoc] = []
    for project in data.get("projects", []):
        docs.append(_project_doc(project))
    for entry in data.get("work", []):
        docs.append(_experience_doc(entry, "work"))
    for entry in data.get("education", []):
        docs.append(_experience_doc(entry, "education"))
    return docs
