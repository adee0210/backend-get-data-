from fastapi import APIRouter, Depends
from typing import Dict, Any
from src.service.monitoring_services import (
    FundingRateMonitoringService,
    BTCDominanceMonitoringService,
    ETFCandlestickMonitoringService,
    get_funding_rate_monitoring_service,
    get_btc_dominance_monitoring_service,
    get_etf_candlestick_monitoring_service,
)


# Create router instance
router = APIRouter(prefix="/crypto/check-data", tags=["crypto-monitoring"])


@router.get("/funding-rate", response_model=Dict[str, Any])
async def check_funding_rate(
    service: FundingRateMonitoringService = Depends(
        get_funding_rate_monitoring_service
    ),
) -> Dict[str, Any]:
    """
    Kiểm tra dữ liệu funding rate theo chu kỳ 8h, 4h, 1h
    - 8h: Kiểm tra theo mốc thời gian 00:00, 08:00, 16:00
    - 4h: Kiểm tra theo mốc thời gian 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
    - 1h: Kiểm tra mỗi giờ
    """
    result = await service.check_funding_rate()
    return result


@router.get("/btc-dominance", response_model=Dict[str, Any])
async def check_btc_dominance(
    service: BTCDominanceMonitoringService = Depends(
        get_btc_dominance_monitoring_service
    ),
) -> Dict[str, Any]:
    """
    Check BTC Dominance có được cập nhật gần đây không
    """
    result = await service.check_btc_dominance()
    return result


@router.get("/etf-candlestick", response_model=Dict[str, Any])
async def check_etf_candlestick(
    service: ETFCandlestickMonitoringService = Depends(
        get_etf_candlestick_monitoring_service
    ),
) -> Dict[str, Any]:
    """
    Check ETF candle stick có được cập nhật gần đây không
    - Kiểm tra tất cả symbols ETF có dữ liệu gần đây không
    """
    result = await service.check_etf_candlestick()
    return result
