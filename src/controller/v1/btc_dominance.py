from fastapi import APIRouter, Depends
from src.service.btc_dominance_service import (
    BTCDominanceService,
    get_btc_dominance_service,
)
from src.dto.btc_dominance_dto import BTCDominanceRequest, BTCDominanceResponse


class BTCDominanceController:
    """Controller for BTC dominance data endpoints"""

    router = APIRouter(
        prefix="/crypto/btc-dominance", tags=["btc-dominance"]
    )

    @router.get("/{days}", response_model=BTCDominanceResponse)
    async def get_btc_dominance_data(
        days: int,
        service: BTCDominanceService = Depends(get_btc_dominance_service),
    ) -> BTCDominanceResponse:
        request = BTCDominanceRequest(days=days)
        response = await service.get_btc_dominance_data(request)
        return response


# Create controller instance  
btc_dominance_controller = BTCDominanceController()