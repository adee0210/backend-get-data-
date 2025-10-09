from pydantic import BaseModel
from typing import Optional
import datetime as dt


class GoldDataModel(BaseModel):
    """Model for gold minute data"""

    datetime: Optional[str] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    close: Optional[float] = None
    volume: Optional[float] = None

    class Config:
        from_attributes = True
