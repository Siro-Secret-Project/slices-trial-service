from typing import Any, Literal, Optional, List
from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    success: bool
    data: Any
    message: str
    status_code: int

class WeightsModel(BaseModel):
    inclusionCriteria: float = Field(0, ge=0, le=1)
    exclusionCriteria: float = Field(0, ge=0, le=1)
    objective: float = Field(0, ge=0, le=1)
    rationale: float = Field(0, ge=0, le=1)
    trialOutcomes: float = Field(0, ge=0, le=1)

class DocumentSearch(BaseModel):
    ecid: str
    userName: str
    rationale: str
    objective: str
    condition: str
    efficacyEndpoints: str
    inclusionCriteria: str
    exclusionCriteria: str
    interventionType: str
    weights: WeightsModel

class GenerateEligibilityCriteria(BaseModel):
    ecid: str
    trialDocuments: list

class DocumentFilters(DocumentSearch):
    phase: List[str]
    country: List[str]
    startDate: Optional[str] = ""
    endDate: Optional[str] = ""
    sponsor: Optional[str] = ""
    sampleSizeMin: Optional[str] = ""
    sampleSizeMax: Optional[str] = ""
    countryLogic: Literal["AND", "OR"] = "OR"
    safetyAssessment: Optional[str] = ""

