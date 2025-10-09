from fastapi import APIRouter, Depends
from typing import Dict, Any
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
    service: ETFCandlestickService = Depends(get_etf_candlestick_service),
) -> ETFCandlestickResponse:
    """
    ETF Candlestick data

    - symbol: Mã ETF (Có sẵn: E1VFVN30, FUEABVND, FUEBFVND, FUEDCMID, FUEFCV50, FUEIP100, FUEKIV30, FUEKIVFS, FUEKIVND, FUEMAV30, FUEMAVND, FUESSV30, FUESSV50, FUESSVFL, FUETCC50, FUEVFVND, FUEVN100)
    - day: Số ngày cần lấy (0=realtime)

    Ví dụ: /crypto/etf-candlestick/?symbol=FUEVN100&day=7
    """
    request = ETFCandlestickRequest(day=day, symbol=symbol)
    result = await service.get_etf_candlestick_data(request)
    return result
