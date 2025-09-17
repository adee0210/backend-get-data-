from fastapi import APIRouter, Depends, BackgroundTasks
from typing import Dict, Any
from src.service.monitoring_service import (
    FundingRateMonitorService,
    get_funding_rate_monitor_service,
)


class MonitoringController:
    """Controller để quản lý monitoring funding rate data"""

    router = APIRouter(prefix="/monitoring/funding_rate", tags=["monitoring"])

    @router.get("/check", response_model=Dict[str, Any])
    async def check_funding_rate_data(
        service: FundingRateMonitorService = Depends(get_funding_rate_monitor_service),
    ) -> Dict[str, Any]:
        """
        Check funding rate data immediately
        """
        result = await service.check_funding_rate_data()
        return result

    @router.get("/status", response_model=Dict[str, Any])
    async def get_monitoring_status(
        service: FundingRateMonitorService = Depends(get_funding_rate_monitor_service),
    ) -> Dict[str, Any]:
        """
        Get current monitoring status
        """
        status = await service.get_monitoring_status()
        return status

    @router.post("/check-async")
    async def check_funding_rate_data_async(
        background_tasks: BackgroundTasks,
        service: FundingRateMonitorService = Depends(get_funding_rate_monitor_service),
    ) -> Dict[str, str]:
        """
        Run funding rate data check in background
        """
        background_tasks.add_task(service.check_funding_rate_data)
        return {"message": "Funding rate data check has been initiated in background"}


# Tạo instance controller để sử dụng trong main.py
monitoring_controller = MonitoringController()
