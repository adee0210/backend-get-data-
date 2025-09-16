from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FundingRate(BaseModel):
    symbol: str
    rate: float
    timestamp: datetime
    source: str  # 'history' hoặc 'realtime'

    class Config:
        from_attributes = True


class RealtimeFundingRate(BaseModel):
    symbol: str
    funding_cap: Optional[float] = None
    funding_floor: Optional[float] = None
    funding_hour: Optional[str] = None
    funding_rate: float
    index_price: float
    interest_rate: Optional[float] = None
    interval: Optional[str] = None
    mark_price: float
    update_date: str  # "2025-09-16"
    update_time: str  # "02:00:09"

    class Config:
        from_attributes = True
