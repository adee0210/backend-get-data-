from fastapi import APIRouter, Depends
from typing import Dict, Any
from src.service.monitoring_services import (
    FundingRateMonitoringService,
    BTCDominanceMonitoringService,
    get_funding_rate_monitoring_service,
    get_btc_dominance_monitoring_service,
)


class MonitoringController:
    """Controller để check funding rate và BTC dominance data riêng biệt"""

    router = APIRouter(prefix="/crypto/monitoring", tags=["crypto-monitoring"])

    @router.get("/funding-rate", response_model=Dict[str, Any])
    async def check_funding_rate(
        service: FundingRateMonitoringService = Depends(get_funding_rate_monitoring_service),
    ) -> Dict[str, Any]:
        """
        Check funding rate data theo chu kỳ 8h, 4h, 1h
        - 8h: Check theo mốc thời gian 00:00, 08:00, 16:00  
        - 4h: Check theo mốc thời gian 00:00, 04:00, 08:00, 12:00, 16:00, 20:00
        - 1h: Check mỗi giờ
        - Tolerance: 30 phút cho mỗi chu kỳ
        - Format: Hiển thị số symbols thiếu data theo từng chu kỳ
        """
        result = await service.check_funding_rate()
        return result

    @router.get("/btc-dominance", response_model=Dict[str, Any])
    async def check_btc_dominance(
        service: BTCDominanceMonitoringService = Depends(get_btc_dominance_monitoring_service),
    ) -> Dict[str, Any]:
        """
        Check BTC dominance có data realtime trong ngày hôm nay không
        - Tìm kiếm records có type: "realtime" 
        - Check xem có data nào trong ngày hôm nay không
        - Trả về cảnh báo nếu không có data realtime trong ngày
        """
        result = await service.check_btc_dominance()
        return result


monitoring_controller = MonitoringController()
