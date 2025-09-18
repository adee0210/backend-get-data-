from fastapi import APIRouter, Depends
from src.service.funding_rate_service import (
    FundingRateService,
    get_funding_rate_service,
)
from src.dto.funding_rate_dto import FundingRateRequest, FundingRateResponse, RealtimeFundingRateRequest, RealtimeFundingRateResponse


class FundingRateController:

    router = APIRouter(
        prefix="/crypto/funding_rate_historical", tags=["funding_rate_historical"]
    )

    @router.get("/{symbols}/{days}", response_model=FundingRateResponse)
    async def get_funding_rate_controller(
        symbols: str,
        days: int,
        service: FundingRateService = Depends(get_funding_rate_service),
    ) -> FundingRateResponse:
        request = FundingRateRequest(symbols=symbols, days=days)
        response = await service.get_funding_rate_data(request)
        return response

class RealtimeFundingRateController:
    router = APIRouter(
        prefix="/crypto/funding_rate_realtime", tags=["funding_rate_realtime"]  
    )

    @router.get("/{symbols}", response_model=RealtimeFundingRateResponse)
    async def get_realtime_funding_rate_controller(
        symbols: str,
        service: FundingRateService = Depends(get_funding_rate_service),
    ) -> RealtimeFundingRateResponse:
        request = RealtimeFundingRateRequest(symbols=symbols)
        response = await service.get_realtime_funding_rate_data(request)
        return response