from pydantic import BaseModel, HttpUrl
from datetime import datetime
from pydantic import BaseModel, ConfigDict, HttpUrl

class AnalysisCreate(BaseModel):
    url: HttpUrl

class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    status: str
    created_at: datetime
    updated_at: datetime