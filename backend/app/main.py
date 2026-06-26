import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure `backend/app/` is on sys.path so bare imports (e.g. `from api.journal
# import ...`) resolve correctly regardless of how uvicorn is invoked.
sys.path.insert(0, str(Path(__file__).parent))

import aiohttp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings

_log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Quiet noisy third-party libraries (Azure SDK HTTP header dumps, etc.) unless
# explicitly debugging, so the app's own INFO/WARNING/ERROR logs are easy to see.
if _log_level > logging.DEBUG:
    for _noisy in ("azure", "openai", "httpx", "httpcore", "urllib3", "aiohttp"):
        logging.getLogger(_noisy).setLevel(logging.WARNING)

from api.contact import router as contact_router
from api.journal import router as journal_router
from api.health import router as health_router
from api.chat import router as chat_router
from core.adapters import ai_search, azure_openai, content_safety
from observability import configure_observability


@asynccontextmanager
async def lifespan(app: FastAPI):
    connector = aiohttp.TCPConnector(limit=20)
    app.state.github_session = aiohttp.ClientSession(connector=connector)

    # Azure OpenAI + AI Search clients for /chat; None when chat isn't configured.
    if settings.chat_configured:
        app.state.openai_client = azure_openai.create_client()
        app.state.search_client = ai_search.create_client()
    else:
        app.state.openai_client = None
        app.state.search_client = None

    # Content Safety is optional; None when not configured (other guardrails remain).
    if settings.safety_configured:
        app.state.content_safety_client = content_safety.ContentSafetyClient()
        logging.getLogger("app.main").info("Content Safety: ENABLED")
    else:
        app.state.content_safety_client = None
        logging.getLogger("app.main").warning(
            "Content Safety: DISABLED (set AZURE_CONTENT_SAFETY_ENDPOINT + _KEY, then restart)"
        )

    yield

    await app.state.github_session.close()
    if app.state.openai_client is not None:
        await app.state.openai_client.close()
    if app.state.search_client is not None:
        await app.state.search_client.close()
    if app.state.content_safety_client is not None:
        await app.state.content_safety_client.close()


# Must run before the app is created so FastAPI gets auto-instrumented.
configure_observability()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(contact_router)
app.include_router(journal_router)
app.include_router(health_router)
app.include_router(chat_router)
