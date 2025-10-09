from fastapi import APIRouter, Depends
from typing import Dict, Any, Optional
from src.service.etf_candlestick_service import (
    ETFCandlestickService,
    get_etf_candlestick_service,
)
from src.dto.etf_candlestick_dto import (
    ETFCandlestickRequest,
    ETFCandlestickResponse,
)


# Create router instance
router = APIRouter(prefix="/crypto/etf-candlestick", tags=["etf-candlestick"])


@router.get("/", response_model=ETFCandlestickResponse)
async def get_etf_candlestick_data(
    symbol: str = "FUEVN100",
    day: int = 1,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    service: ETFCandlestickService = Depends(get_etf_candlestick_service),
) -> ETFCandlestickResponse:
    """
    ETF Candlestick data

    Tham số:
    - symbol: E1VFVN30, FUEABVND, FUEBFVND, FUEDCMID, FUEFCV50, FUEIP100, FUEKIV30, FUEKIVFS, FUEKIVND, FUEMAV30, FUEMAVND, FUESSV30, FUESSV50, FUESSVFL, FUETCC50, FUEVFVND, FUEVN100

    - /crypto/etf-candlestick/?symbol=symbol&days=7 : Tham số days : Số ngày gần nhất (days = 0 : realtime)
    - /crypto/etf-candlestick/?symbol=symbol&from_date=10092025&to_date=12092025 : tham số from_date , to_date format DDMMYYYY. from_date < to_date
    """
    request = ETFCandlestickRequest(
        day=day, symbol=symbol, from_date=from_date, to_date=to_date
    )
    result = await service.get_etf_candlestick_data(request)
    return result
