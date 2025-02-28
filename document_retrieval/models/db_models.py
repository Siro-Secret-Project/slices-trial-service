from datetime import datetime
from pydantic import BaseModel

class StoreEligibilityCriteria(BaseModel):
    ecid: str
    categorizedData: dict
    userCategorizedData: dict
    metrics: dict
    createdAt: datetime
    updatedAt: datetime

class StoreSimilarTrials(BaseModel):
    ecid: str
    userName: str
    userInput: dict
    similarTrials: list
    createdAt: datetime
    updatedAt: datetime

class NotificationData(BaseModel):
    ecid: str
    userName: str
    notificationMessage: str
    seen: bool = False
    createdAt: datetime
    updatedAt: datetime

class WorkflowStates(BaseModel):
    ecid: str
    step: str
    status: str
    createdAt: datetime
    updatedAt: datetime