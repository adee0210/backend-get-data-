from pydantic import BaseModel
from typing import List, Optional
from src.model.etf_candlestick import ETFCandlestickModel, RealtimeETFCandlestickModel


class ETFCandlestickRequest(BaseModel):
    """Request model for historical ETF candlestick data"""
    day: int = 1
    symbol: str = "SPY"  # Default symbol
    
    class Config:
        json_schema_extra = {
            "example": {
                "day": 7,
                "symbol": "SPY"
            }
        }


class ETFCandlestickResponse(BaseModel):
    """Response model for historical ETF candlestick data"""
    data: List[ETFCandlestickModel]
    total_records: int
    request_day: int
    request_symbol: str
    
    class Config:
        from_attributes = True


class RealtimeETFCandlestickRequest(BaseModel):
    """Request model for realtime ETF candlestick data (day=0)"""
    day: int = 0
    symbol: str = "SPY"  # Default symbol
    
    class Config:
        json_schema_extra = {
            "example": {
                "day": 0,
                "symbol": "SPY"
            }
        }


class RealtimeETFCandlestickResponse(BaseModel):
    """Response model for realtime ETF candlestick data"""
    data: List[RealtimeETFCandlestickModel]
    total_records: int
    request_day: int
    request_symbol: str
    
    class Config:
        from_attributes = True