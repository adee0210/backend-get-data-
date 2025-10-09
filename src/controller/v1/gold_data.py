from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from datetime import datetime, timedelta
from src.service.gold_data_service import (
    GoldDataService,
    get_gold_data_service,
)
from src.dto.gold_data_dto import GoldDataRequest, GoldDataResponse


# Create router instance
router = APIRouter(prefix="/crypto/gold-data", tags=["gold-data"])


@router.get("/", response_model=GoldDataResponse)
async def get_gold_data(
    day: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    service: GoldDataService = Depends(get_gold_data_service),
) -> GoldDataResponse:
    """
    GOLD DATA
    - /crypto/gold-data/?day=7 : Parameter day : Number of recent days (day = 0 : realtime)
    - /crypto/gold-data/?from_date=10092025&to_date=12092025 : Parameters from_date , to_date format DDMMYYYY. from_date < to_date

    Can use day or from_date & to_date or all 3 parameters.
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

        # Nếu có cả 3 tham số, kiểm tra day có trong khoảng from_date đến to_date
        if day is not None:
            # day = 1 nghĩa là 1 ngày gần nhất từ to_date
            calculated_from = to_dt - timedelta(days=day)
            if calculated_from < from_dt:
                raise HTTPException(
                    status_code=400, detail=f"day={day} extends beyond from_date range"
                )

    elif day is None:
        # Nếu không có tham số nào, mặc định day=1
        day = 1

    request = GoldDataRequest(day=day, from_date=from_date, to_date=to_date)
    result = await service.get_gold_data(request)
    return result
