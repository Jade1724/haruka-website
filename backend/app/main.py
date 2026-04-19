from fastapi import FastAPI

from api.journal import router as journal_router

app = FastAPI()

app.include_router(journal_router)
