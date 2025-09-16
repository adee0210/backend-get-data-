# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
from fastapi import FastAPI

from src.controller.v1.funding_rate import FundingRateController
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


app = FastAPI()
app.include_router(FundingRateController.router)
