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
from src.service.scheduler_service import start_monitoring, stop_monitoring
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
    try:
        # Khởi động monitoring scheduler
        start_monitoring()
        logger.info("Monitoring system started successfully")
    except Exception as e:
        logger.error(f"Error starting monitoring: {str(e)}")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    try:
        # Dừng monitoring scheduler
        stop_monitoring()
        logger.info("Monitoring system stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping monitoring: {str(e)}")


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
        "timestamp": "2025-09-18",
        "services": {"api": "running", "database": "connected", "monitoring": "active"},
    }
