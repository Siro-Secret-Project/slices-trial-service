from datetime import datetime
from pydantic import BaseModel

class StoreEligibilityCriteria(BaseModel):
    ecid: str
    inclusion_criteria: list
    exclusion_criteria: list
    created_at: datetime
    updated_at: datetime
    categorizedData: dict
    userCategorizedData: dict
    trailDocuments: list
