from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FundingRate(BaseModel):
    symbol: str
    rate: float
    timestamp: datetime
    source: str  # 'history' or 'realtime'

    class Config:
        from_attributes = True
