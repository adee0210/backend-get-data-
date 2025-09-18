from typing import List, Dict, Any  
from pydantic import BaseModel

from src.model.btc_dominance import RealtimeBTCDominanceModel


class BTCDominanceRequest(BaseModel):
    days: int

class BTCDominanceResponse(BaseModel):
    data: List[Dict[str, Any]]

class RealtimeBTCDominanceRequest(BaseModel):
    pass

class RealtimeBTCDominanceResponse(BaseModel):
    data: List[Dict[str, Any]]