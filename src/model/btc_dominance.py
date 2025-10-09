from pydantic import BaseModel
import datetime as dt
from typing import Optional


class BTCDominanceModel(BaseModel):
    _id: Optional[str] = None
    timestamp_ms: Optional[int] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    datetime: Optional[str] = None  # Format: YYYY-MM-DD

    class Config:
        from_attributes = True


class RealtimeBTCDominanceModel(BaseModel):
    _id: Optional[str] = None
    timestamp_ms: Optional[int] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None
    datetime: Optional[str] = None  # Format: YYYY-MM-DD

    class Config:
        from_attributes = True
        

