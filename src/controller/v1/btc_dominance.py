from fastapi import APIRouter, Depends
from src.service.btc_dominance_service import (
    BTCDominanceService,
    get_btc_dominance_service,
)
from src.dto.btc_dominance_dto import BTCDominanceRequest, BTCDominanceResponse, RealtimeBTCDominanceRequest, RealtimeBTCDominanceResponse


class BTCDominanceController:
    router = APIRouter(
        prefix="/crypto/btc_dominance_historical", tags=["btc_dominance_historical"]
    )

    @router.get("/{days}", response_model=BTCDominanceResponse)
    async def get_btc_dominance_controller(
        days: int,
        service: BTCDominanceService = Depends(get_btc_dominance_service),
    ) -> BTCDominanceResponse:
        request = BTCDominanceRequest(days=days)
        response = await service.get_historical_btc_dominance_data(request)
        return response


class RealtimeBTCDominanceController:
    router = APIRouter(
        prefix="/crypto/btc_dominance_realtime", tags=["btc_dominance_realtime"]
    )

    @router.get("/", response_model=RealtimeBTCDominanceResponse)
    async def get_realtime_btc_dominance_controller(
        service: BTCDominanceService = Depends(get_btc_dominance_service),
    ) -> RealtimeBTCDominanceResponse:
        request = RealtimeBTCDominanceRequest()
        response = await service.get_realtime_btc_dominance_data(request)
        return response