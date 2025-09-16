from pydantic import BaseModel
from typing import List, Dict, Any


class FundingRateRequest(BaseModel):
    symbols: str
    days: int


class FundingRateResponse(BaseModel):
    data: List[Dict[str, Any]]
