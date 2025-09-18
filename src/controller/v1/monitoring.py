from fastapi import APIRouter, Depends
from typing import Dict, Any
from src.service.monitoring_services import (
    FundingRateMonitoringService,
    BTCDominanceMonitoringService,
    get_funding_rate_monitoring_service,
    get_btc_dominance_monitoring_service,
)


class MonitoringController:

    router = APIRouter(prefix="/crypto/monitoring", tags=["crypto-monitoring"])

    @router.get("/funding-rate", response_model=Dict[str, Any])
    async def check_funding_rate(
        service: FundingRateMonitoringService = Depends(get_funding_rate_monitoring_service),
    ) -> Dict[str, Any]:
        result = await service.check_funding_rate()
        return result

    @router.get("/btc-dominance", response_model=Dict[str, Any])
    async def check_btc_dominance(
        service: BTCDominanceMonitoringService = Depends(get_btc_dominance_monitoring_service),
    ) -> Dict[str, Any]:
        result = await service.check_btc_dominance()
        return result


monitoring_controller = MonitoringController()
