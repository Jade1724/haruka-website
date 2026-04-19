from contextlib import asynccontextmanager

import aiohttp
from fastapi import FastAPI

from api.journal import router as journal_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    connector = aiohttp.TCPConnector(limit=20)
    app.state.github_session = aiohttp.ClientSession(connector=connector)
    yield
    await app.state.github_session.close()


app = FastAPI(lifespan=lifespan)

app.include_router(journal_router)
