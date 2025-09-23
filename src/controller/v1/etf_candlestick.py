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


class ETFCandlestickController:
    """Controller for ETF candlestick data endpoints"""

    router = APIRouter(prefix="/crypto/etf-candlestick", tags=["etf-candlestick"])

    @router.get("/{symbol}/{day}", response_model=ETFCandlestickResponse)
    async def get_etf_candlestick_data(
        day: int,
        symbol: str,
        service: ETFCandlestickService = Depends(get_etf_candlestick_service),
    ) -> ETFCandlestickResponse:
        """
        Symbol:E1VFVN30, FUEABVND, FUEBFVND, FUEDCMID, FUEFCV50, FUEIP100, FUEKIV30, FUEKIVFS, FUEKIVND, FUEMAV30, FUEMAVND, FUESSV30, FUESSV50, FUESSVFL, FUETCC50, FUEVFVND, FUEVN100
        """
        request = ETFCandlestickRequest(day=day, symbol=symbol)
        result = await service.get_etf_candlestick_data(request)
        return result


# Create controller instance
etf_candlestick_controller = ETFCandlestickController()