from typing import Any, Optional
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
    eligibilityCriteria: Optional[dict]

class SearchDocuments(BaseModel):
    inclusionCriteria: str
    exclusionCriteria: str
    rationale: str
    objective: str
    efficacyEndpoints: str