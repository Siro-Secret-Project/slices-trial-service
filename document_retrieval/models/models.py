from typing import Literal, Any, Optional
from pydantic import BaseModel

class SearchResult(BaseModel):
    search_query: str
    embedding_model: Literal["OpenAI", "BioBert"]
    module: Optional[str] = "conditionsModule"
    similarity_threshold: int = 50

class BaseResponse(BaseModel):
    success: bool
    data: Any
    message: str
    status_code: int