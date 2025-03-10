from typing import Any, Literal, Optional, List, Dict
from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    success: bool
    data: Any
    message: str
    status_code: int

class WeightsModel(BaseModel):
    inclusionCriteria: float = Field(0, ge=0, le=1)
    exclusionCriteria: float = Field(0, ge=0, le=1)
    condition: float = Field(0, ge=0, le=1)
    title: float = Field(0, ge=0, le=1)
    trialOutcomes: float = Field(0, ge=0, le=1)

class DocumentSearch(BaseModel):
    ecid: str
    userName: str
    rationale: str
    objective: str
    condition: str
    title: str
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


class DraftEligibilityCriteria(BaseModel):
    sample_trial_rationale: str
    similar_trial_documents: Dict
    user_provided_inclusion_criteria: str
    user_provided_exclusion_criteria: str
    user_provided_trial_conditions: str
    user_provided_trial_outcome: str
    generated_inclusion_criteria: List
    generated_exclusion_criteria: List

