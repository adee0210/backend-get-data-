from fastapi import APIRouter, Depends
from src.service.btc_dominance_service import (
    BTCDominanceService,
    get_btc_dominance_service,
)
from src.dto.btc_dominance_dto import BTCDominanceRequest, BTCDominanceResponse


# Create router instance
router = APIRouter(prefix="/crypto/btc-dominance", tags=["btc-dominance"])


@router.get("/", response_model=BTCDominanceResponse)
async def get_btc_dominance_data(
    days: int = 1,
    service: BTCDominanceService = Depends(get_btc_dominance_service),
) -> BTCDominanceResponse:
    """
    BTC Dominance Data

    Tham số:
    - days: Số ngày cần lấy (0: realtime)

    Ví dụ: /crypto/btc-dominance/?days=7
    """
    request = BTCDominanceRequest(days=days)
    response = await service.get_btc_dominance_data(request)
    return response
