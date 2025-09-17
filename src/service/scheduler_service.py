import asyncio
import schedule
import time
import threading
from datetime import datetime
from src.service.monitoring_service import (
    FundingRateMonitorService,
    get_funding_rate_monitor_service,
)
from src.config.variable_config import MONITORING_CONFIG
from src.config.logger_config import logger


class MonitoringScheduler:
    """Scheduler để chạy monitoring funding rate định kỳ"""

    def __init__(self, monitoring_service: FundingRateMonitorService = None):
        self.monitoring_service = (
            monitoring_service or get_funding_rate_monitor_service()
        )
        self.check_interval = MONITORING_CONFIG.get(
            "funding_rate_check_interval", 3600
        )  # seconds
        self.is_running = False
        self.scheduler_thread = None

    def _run_check(self):
        """Chạy kiểm tra funding rate data (sync wrapper cho async function)"""
        try:
            # Tạo event loop mới cho thread nếu cần
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Chạy kiểm tra
            result = loop.run_until_complete(
                self.monitoring_service.check_funding_rate_data()
            )
            logger.info(
                f"Monitoring check completed: {result.get('status', 'UNKNOWN')}"
            )

        except Exception as e:
            logger.error(f"Error in monitoring scheduler: {str(e)}")

    def start_scheduler(self):
        """Khởi động scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return

        # Cấu hình schedule
        schedule.every(self.check_interval).seconds.do(self._run_check)

        # Chạy kiểm tra ngay lập tức
        logger.info("Running initial funding rate check...")
        self._run_check()

        # Khởi động scheduler trong thread riêng
        self.is_running = True
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler_loop, daemon=True
        )
        self.scheduler_thread.start()

        logger.info(
            f"Monitoring scheduler started, checking every {self.check_interval} seconds"
        )

    def _run_scheduler_loop(self):
        """Vòng lặp chính của scheduler"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every 1 minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)

    def stop_scheduler(self):
        """Dừng scheduler"""
        self.is_running = False
        schedule.clear()

        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)

        logger.info("Monitoring scheduler stopped")

    def get_status(self) -> dict:
        """Lấy trạng thái scheduler"""
        return {
            "is_running": self.is_running,
            "check_interval_seconds": self.check_interval,
            "next_run": schedule.next_run() if schedule.jobs else None,
            "total_jobs": len(schedule.jobs),
        }


# Global scheduler instance
_scheduler_instance = None


def get_monitoring_scheduler() -> MonitoringScheduler:
    """Singleton pattern cho MonitoringScheduler"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = MonitoringScheduler()
    return _scheduler_instance


def start_monitoring():
    """Khởi động monitoring system"""
    scheduler = get_monitoring_scheduler()
    scheduler.start_scheduler()


def stop_monitoring():
    """Dừng monitoring system"""
    scheduler = get_monitoring_scheduler()
    scheduler.stop_scheduler()
