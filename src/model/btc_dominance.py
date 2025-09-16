from pydantic import BaseModel
from datetime import datetime


class BTCDominanceModel(BaseModel):
    open:float
    high:float
    low:float
    close:float
    volume:float
    datetime:datetime

    class Config:
        from_attributes = True


class RealtimeBTCDominanceModel(BaseModel):
    open:float
    high:float
    low:float
    close:float
    volume:float
    datetime:datetime

    class Config:
        from_attributes = True
        

