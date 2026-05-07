from pydantic import BaseModel


class SearchRequest(BaseModel):
    indicator: str


class BatchSearchRequest(BaseModel):
    indicators: list[str]