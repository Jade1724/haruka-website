from datetime import date

from fastapi import APIRouter, HTTPException

from models.journal import JournalDetail, JournalSummary

router = APIRouter(prefix="/journals", tags=["journals"])


# Placeholder data — replace with Obsidian/GitHub scraper service
_journals: list[JournalDetail] = [
    JournalDetail(
        id="setting-up-nextjs-with-fastapi",
        title="Setting up Next.js with a FastAPI backend",
        published_on=date(2024, 11, 3),
        updated_on=date(2024, 11, 5),
        content=(
            "Getting a Next.js frontend talking to a FastAPI backend turned out to be "
            "straightforward, but there were a few gotchas worth documenting.\n\n"
            "The first issue was CORS. FastAPI doesn't enable it by default, so any fetch "
            "from the browser gets blocked immediately. Adding CORSMiddleware with the right "
            "origins fixed it.\n\n"
            "The second issue was environment variables. Next.js only exposes variables "
            "prefixed with NEXT_PUBLIC_ to the browser."
        ),
    ),
    JournalDetail(
        id="tailwind-v4-migration",
        title="What changed moving to Tailwind CSS v4",
        published_on=date(2024, 11, 18),
        updated_on=date(2024, 11, 18),
        content=(
            "Tailwind v4 is a significant departure from v3. Configuration moved out of "
            "tailwind.config.js and into CSS using @theme {} blocks.\n\n"
            "The color system now uses oklch by default. The PostCSS plugin is now "
            "@tailwindcss/postcss instead of tailwindcss directly."
        ),
    ),
    JournalDetail(
        id="obsidian-github-scraper",
        title="Scraping my Obsidian vault from GitHub",
        published_on=date(2024, 12, 1),
        updated_on=date(2024, 12, 9),
        content=(
            "My notes live in a private Obsidian vault synced to GitHub. The goal was to "
            "surface selected notes as journal entries without making the whole vault public.\n\n"
            "The approach: a FastAPI endpoint calls the GitHub Contents API, fetches specific "
            "markdown files, parses frontmatter with python-frontmatter, and returns structured JSON."
        ),
    ),
]

_journals_by_id: dict[str, JournalDetail] = {j.id: j for j in _journals}


@router.get("", response_model=list[JournalSummary])
def get_journals() -> list[JournalDetail]:
    return _journals


@router.get("/{journal_id}", response_model=JournalDetail)
def get_journal(journal_id: str) -> JournalDetail:
    journal = _journals_by_id.get(journal_id)
    if journal is None:
        raise HTTPException(status_code=404, detail="Journal not found")
    return journal
