from fastapi import APIRouter, Depends
from src.service.funding_rate_service import (
    FundingRateService,
    get_funding_rate_service,
)
from src.dto.funding_rate_dto import FundingRateRequest, FundingRateResponse


class FundingRateController:
    """A class-style controller similar to a Spring Boot @RestController.

    Exposes endpoints under `/funding_rate_historical` and delegates to
    `FundingRateService` for business logic.
    """

    router = APIRouter(
        prefix="/funding_rate_historical", tags=["funding_rate_historical"]
    )

    @router.get("/{symbols}/{days}", response_model=FundingRateResponse)
    async def get_funding_rate_controller(
        symbols: str,
        days: int,
        service: FundingRateService = Depends(get_funding_rate_service),
    ) -> FundingRateResponse:
        """Get historical funding rates for `symbols` (comma-separated) for the last `days` days.

        Example: `/funding_rate_historical/BTCUSDT,ETHUSDT/7`
        """
        request = FundingRateRequest(symbols=symbols, days=days)
        response = await service.get_funding_rate_data(request)
        return response

    @router.get("/", response_model=FundingRateResponse)
    async def get_funding_rate_query(
        symbols: str | None = None,
        days: int | None = None,
        day: int | None = None,  # support alias `day` used in your request
        service: FundingRateService = Depends(get_funding_rate_service),
    ) -> FundingRateResponse:
        """Query endpoint that accepts `?symbols=BTCUSDT&days=10` or `?symbols=BTCUSDT&day=10`.

        This avoids 404s when clients prefer query parameters instead of path params.
        """
        if symbols is None:
            # FastAPI will normally validate required params; return empty response
            return FundingRateResponse(data=[])

        used_days = days if days is not None else (day if day is not None else 1)
        request = FundingRateRequest(symbols=symbols, days=used_days)
        response = await service.get_funding_rate_data(request)
        return response
