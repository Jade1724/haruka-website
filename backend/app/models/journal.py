from datetime import date

from pydantic import BaseModel


class JournalSummary(BaseModel):
    id: str
    title: str
    published_on: date
    updated_on: date


class JournalDetail(JournalSummary):
    content: str
