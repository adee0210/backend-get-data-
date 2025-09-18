# uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.controller.v1.btc_dominance import (
    BTCDominanceController,
    RealtimeBTCDominanceController,
)
from src.controller.v1.funding_rate import (
    FundingRateController,
    RealtimeFundingRateController,
)
from src.controller.v1.monitoring import monitoring_controller
from src.config.logger_config import logger
import sys
import os

# Thêm đường dẫn gốc vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Quản lý lifecycle của ứng dụng"""
    # Startup
    logger.info("Starting application...")
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    logger.info("Application stopped successfully")


app = FastAPI(
    title="Crypto Data API",
    description="API for cryptocurrency funding rate and BTC dominance data",
    version="1.0.0",
    lifespan=lifespan,
)

# Include routers
app.include_router(FundingRateController.router)
app.include_router(BTCDominanceController.router)
app.include_router(RealtimeFundingRateController.router)
app.include_router(RealtimeBTCDominanceController.router)
app.include_router(monitoring_controller.router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Crypto Data API is running", "status": "OK", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": "2025-09-18T00:00:00Z",
        "services": {
            "api": "running", 
            "database": "connected", 
            "monitoring": "available"
        },
    }
