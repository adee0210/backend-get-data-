from typing import List, Dict, Any  # Sửa từ ast sang typing
from pydantic import BaseModel

from src.model.btc_dominance import RealtimeBTCDominanceModel


class BTCDominanceRequest(BaseModel):
    days: int

class BTCDominanceResponse(BaseModel):
    data: List[Dict[str, Any]]

class RealtimeBTCDominanceRequest(BaseModel):
    # Realtime không cần days, chỉ lấy data mới nhất
    pass

class RealtimeBTCDominanceResponse(BaseModel):
    # Có thể trả về dicts (sau .model_dump()) hoặc model instances
    data: List[Dict[str, Any]]