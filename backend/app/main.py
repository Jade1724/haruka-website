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

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from api.contact import router as contact_router
from api.journal import router as journal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    connector = aiohttp.TCPConnector(limit=20)
    app.state.github_session = aiohttp.ClientSession(connector=connector)
    yield
    await app.state.github_session.close()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(contact_router)
app.include_router(journal_router)
