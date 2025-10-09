from pydantic import BaseModel
from typing import List, Optional
from src.model.etf_candlestick import ETFCandlestickModel, RealtimeETFCandlestickModel


class ETFCandlestickRequest(BaseModel):
    """Request model for historical ETF candlestick data"""

    day: int = 1
    symbol: str = "SPY"  # Default symbol
    from_date: Optional[str] = None
    to_date: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "day": 7,
                "symbol": "SPY",
                "from_date": "10092025",
                "to_date": "12092025",
            }
        }


class ETFCandlestickResponse(BaseModel):
    """Response model for historical ETF candlestick data"""

    data: List[ETFCandlestickModel]

    class Config:
        from_attributes = True


class RealtimeETFCandlestickRequest(BaseModel):
    """Request model for realtime ETF candlestick data (day=0)"""

    day: int = 0
    symbol: str = "SPY"  # Default symbol

    class Config:
        json_schema_extra = {"example": {"day": 0, "symbol": "SPY"}}


class RealtimeETFCandlestickResponse(BaseModel):
    """Response model for realtime ETF candlestick data"""

    data: List[RealtimeETFCandlestickModel]

    class Config:
        from_attributes = True
