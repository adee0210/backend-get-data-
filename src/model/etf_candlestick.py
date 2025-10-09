from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ETFCandlestickModel(BaseModel):
    """Model for ETF candlestick data"""
    symbol: str
    open: float
    high: float 
    low: float
    close: float
    volume: float
    datetime: str
    _id: Optional[str] = None

    class Config:
        from_attributes = True


class RealtimeETFCandlestickModel(BaseModel):
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    datetime: str
    _id: Optional[str] = None

    class Config:
        from_attributes = True