from fastapi import APIRouter, Depends
from src.service.gold_data_service import (
    GoldDataService,
    get_gold_data_service,
)
from src.dto.gold_data_dto import GoldDataRequest, GoldDataResponse


# Create router instance
router = APIRouter(prefix="/crypto/gold-data", tags=["gold-data"])


@router.get("/", response_model=GoldDataResponse)
async def get_gold_data(
    day: int = 1,
    service: GoldDataService = Depends(get_gold_data_service),
) -> GoldDataResponse:
    """
    Gold data

    Tham số:
    - day: Số ngày cần lấy (0=realtime)

    Ví dụ: /crypto/gold-data/?day=7
    """
    request = GoldDataRequest(day=day)
    result = await service.get_gold_data(request)
    return result
