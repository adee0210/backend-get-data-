# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
from fastapi import FastAPI

from src.controller.v1.btc_dominance import BTCDominanceController, RealtimeBTCDominanceController
from src.controller.v1.funding_rate import FundingRateController, RealtimeFundingRateController
import sys
import os

# Thêm đường dẫn gốc vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


app = FastAPI()
app.include_router(FundingRateController.router)
app.include_router(BTCDominanceController.router)
app.include_router(RealtimeFundingRateController.router)
app.include_router(RealtimeBTCDominanceController.router)
