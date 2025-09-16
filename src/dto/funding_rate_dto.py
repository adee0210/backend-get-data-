from pydantic import BaseModel
from typing import List, Dict, Any
from src.model.funding_rate import RealtimeFundingRate


class FundingRateRequest(BaseModel):
    symbols: str
    days: int


class FundingRateResponse(BaseModel):
    data: List[Dict[str, Any]]


class RealtimeFundingRateRequest(BaseModel):
    symbols: str


class RealtimeFundingRateResponse(BaseModel):
    data: List[RealtimeFundingRate]
