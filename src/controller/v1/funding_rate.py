from fastapi import APIRouter, Depends
from src.service.funding_rate_service import (
    FundingRateService,
    get_funding_rate_service,
)
from src.dto.funding_rate_dto import (
    FundingRateRequest,
    FundingRateResponse,
    RealtimeFundingRateRequest,
    RealtimeFundingRateResponse,
)


# Historical Funding Rate Router
funding_rate_router = APIRouter(
    prefix="/crypto/funding_rate_historical", tags=["funding_rate_historical"]
)


@funding_rate_router.get("/", response_model=FundingRateResponse)
async def get_funding_rate_controller(
    symbols: str = "BTCUSDT",
    days: int = 1,
    service: FundingRateService = Depends(get_funding_rate_service),
) -> FundingRateResponse:
    """
    Lấy dữ liệu lịch sử funding rate

    Tham số:
    - symbols: Lấy nhiều hơn 2 mã giao dịch cách nhau bởi dấu phẩy (ví dụ: "BTCUSDT,ETHUSDT")
    - days: Số ngày cần lấy

    Ví dụ: /crypto/funding_rate_historical/?symbols=BTCUSDT,ETHUSDT&days=7
    """
    request = FundingRateRequest(symbols=symbols, days=days)
    response = await service.get_funding_rate_data(request)
    return response


# Realtime Funding Rate Router
realtime_funding_rate_router = APIRouter(
    prefix="/crypto/funding_rate_realtime", tags=["funding_rate_realtime"]
)


@realtime_funding_rate_router.get("/", response_model=RealtimeFundingRateResponse)
async def get_realtime_funding_rate_controller(
    symbols: str = "BTCUSDT",
    service: FundingRateService = Depends(get_funding_rate_service),
) -> RealtimeFundingRateResponse:
    """
    realtime funding rate data

    Tham số:
    - symbols: Lấy nhiều hơn 2 mã giao dịch thì viết cách nhau bởi dấu phẩy (ví dụ: "BTCUSDT,ETHUSDT")

    Ví dụ: /crypto/funding_rate_realtime/?symbols=BTCUSDT,ETHUSDT
    """
    request = RealtimeFundingRateRequest(symbols=symbols)
    response = await service.get_realtime_funding_rate_data(request)
    return response


# Backward compatibility
class FundingRateController:
    router = funding_rate_router


class RealtimeFundingRateController:
    router = realtime_funding_rate_router
