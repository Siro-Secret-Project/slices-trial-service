from datetime import datetime
from pydantic import BaseModel

class StoreEligibilityCriteria(BaseModel):
    ecid: str
    categorizedData: dict
    userCategorizedData: dict
    created_at: datetime
    updated_at: datetime

class StoreSimilarTrials(BaseModel):
    ecid: str
    userName: str
    userInput: dict
    similarTrials: list
    created_at: datetime
    updated_at: datetime