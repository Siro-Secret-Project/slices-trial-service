from typing import Any
from pydantic import BaseModel

class SearchResult(BaseModel):
    search_query: str
    module: str = None
    similarity_threshold: int = 50

class BaseResponse(BaseModel):
    success: bool
    data: Any
    message: str
    status_code: int

class SearchDocuments(BaseModel):
    inclusion_criteria: str
    exclusion_criteria: str
    rationale: str