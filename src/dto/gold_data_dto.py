from pydantic import BaseModel
from typing import List
from src.model.gold_data import GoldDataModel


class GoldDataRequest(BaseModel):
    """Request model for gold data"""

    day: int = 1

    class Config:
        json_schema_extra = {"example": {"day": 7}}


class GoldDataResponse(BaseModel):
    """Response model for gold data"""

    data: List[GoldDataModel]

    class Config:
        from_attributes = True
