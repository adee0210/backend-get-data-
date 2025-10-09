from pydantic import BaseModel
from typing import List, Optional
from src.model.gold_data import GoldDataModel


class GoldDataRequest(BaseModel):
    """Request model for gold data"""

    day: Optional[int] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {"day": 7, "from_date": "10092025", "to_date": "12092025"}
        }


class GoldDataResponse(BaseModel):
    """Response model for gold data"""

    data: List[GoldDataModel]

    class Config:
        from_attributes = True
