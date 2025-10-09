from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from src.service.btc_dominance_service import (
    BTCDominanceService,
    get_btc_dominance_service,
)
from src.dto.btc_dominance_dto import BTCDominanceRequest, BTCDominanceResponse


# Create router instance
router = APIRouter(prefix="/crypto/btc-dominance", tags=["btc-dominance"])


@router.get("/", response_model=BTCDominanceResponse)
async def get_btc_dominance_data(
    days: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    service: BTCDominanceService = Depends(get_btc_dominance_service),
) -> BTCDominanceResponse:
    """
    BTC DOMINANCE DATA
    - /crypto/btc-dominance/?days=7 : Tham số days : Số ngày gần nhất (days = 0 : realtime)
    - /crypto/btc-dominance/?from_date=10092025&to_date=12092025 : tham số from_date , to_date format DDMMYYYY. from_date < to_date

    Có thể sử dụng days hoặc from_date & to_date hoặc cả 3 tham số.
    """

    # Validation logic
    if from_date is not None or to_date is not None:
        # Nếu có from_date hoặc to_date thì phải có đủ cả hai
        if from_date is None or to_date is None:
            raise HTTPException(
                status_code=400,
                detail="Both from_date and to_date are required when using date range",
            )

        # Validate date format DDMMYYYY
        try:
            from_dt = datetime.strptime(from_date, "%d%m%Y")
            to_dt = datetime.strptime(to_date, "%d%m%Y")
        except ValueError:
            raise HTTPException(
                status_code=400, detail="Invalid date format. Use DDMMYYYY format"
            )

        # Check from_date < to_date
        if from_dt >= to_dt:
            raise HTTPException(
                status_code=400, detail="from_date must be less than to_date"
            )

        # Nếu có cả 3 tham số, kiểm tra days có trong khoảng from_date đến to_date
        if days is not None:
            # days = 1 nghĩa là 1 ngày gần nhất từ to_date
            calculated_from = to_dt - timedelta(days=days)
            if calculated_from < from_dt:
                raise HTTPException(
                    status_code=400,
                    detail=f"days={days} extends beyond from_date range",
                )

    elif days is None:
        # Nếu không có tham số nào, mặc định days=1
        days = 1

    request = BTCDominanceRequest(days=days, from_date=from_date, to_date=to_date)
    response = await service.get_btc_dominance_data(request)
    return response
