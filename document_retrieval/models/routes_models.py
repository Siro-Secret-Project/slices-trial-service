from typing import Any
from pydantic import BaseModel, Field

class WeightsModel(BaseModel):
    inclusionCriteria: float = Field(0.2, ge=0, le=1)
    exclusionCriteria: float = Field(0.2, ge=0, le=1)
    objective: float = Field(0.2, ge=0, le=1)
    rationale: float = Field(0.2, ge=0, le=1)
    trialOutcomes: float = Field(0.2, ge=0, le=1)


class BaseResponse(BaseModel):
    success: bool
    data: Any
    message: str
    status_code: int

class SimilarDocuments(BaseModel):
    inclusionCriteria: str
    exclusionCriteria: str
    rationale: str
    objective: str
    efficacyEndpoints: str

class GenerateEligibilityCriteria(SimilarDocuments):
    ecid: str

class DocumentSearch(SimilarDocuments):
    weights: WeightsModel