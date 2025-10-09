from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from src.model.btc_dominance import RealtimeBTCDominanceModel


class BTCDominanceRequest(BaseModel):
    days: Optional[int] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None


class BTCDominanceResponse(BaseModel):
    data: List[Dict[str, Any]]


class RealtimeBTCDominanceRequest(BaseModel):
    pass


class RealtimeBTCDominanceResponse(BaseModel):
    data: List[Dict[str, Any]]
