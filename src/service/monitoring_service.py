import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from src.config.variable_config import MONITORING_CONFIG
from src.config.logger_config import logger
from src.service.telegram_service import TelegramService, get_telegram_service
from src.service.funding_rate_service import (
    FundingRateService,
    get_funding_rate_service,
)


class FundingRateMonitorService:
    """Service để monitor funding rate data và gửi cảnh báo"""

    def __init__(
        self,
        funding_service: FundingRateService = None,
        telegram_service: TelegramService = None,
    ):
        self.funding_service = funding_service or get_funding_rate_service()
        self.telegram_service = telegram_service or get_telegram_service()
        self.expected_symbols = MONITORING_CONFIG.get("expected_symbols", [])
        self.api_check_url = MONITORING_CONFIG.get("api_check_url")
        self.tolerance_minutes = MONITORING_CONFIG.get("tolerance_minutes", 30)

    def _get_expected_funding_times(self) -> List[str]:
        """
        Tính toán các mốc thời gian funding rate dự kiến trong ngày
        Funding rate thường được cập nhật mỗi 8 giờ: 00:00, 08:00, 16:00
        """
        return ["00:00:00", "08:00:00", "16:00:00"]

    def _get_current_funding_schedule(self) -> Tuple[str, str, bool]:
        """
        Get current funding rate schedule and check if we should alert

        Returns:
            Tuple of (date_string, time_string, should_check)
            should_check is True if we're past a funding time and within tolerance
        """
        now = datetime.now()
        funding_times = self._get_expected_funding_times()
        today = now.strftime("%Y-%m-%d")

        # Check if we're within tolerance of any funding time today
        for time_str in funding_times:
            expected_datetime = datetime.strptime(
                f"{today} {time_str}", "%Y-%m-%d %H:%M:%S"
            )

            # If we're past the funding time but within tolerance window
            if (
                expected_datetime
                <= now
                <= expected_datetime + timedelta(minutes=self.tolerance_minutes)
            ):
                return today, time_str, True

        # If no current funding time, return the next one (for status display)
        for time_str in funding_times:
            expected_datetime = datetime.strptime(
                f"{today} {time_str}", "%Y-%m-%d %H:%M:%S"
            )
            if now < expected_datetime:
                return today, time_str, False

        # If all times today have passed, return first time tomorrow
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        return tomorrow, funding_times[0], False

    async def _check_api_data(self, symbols: List[str]) -> Dict[str, Optional[Dict]]:
        """
        Kiểm tra data từ API của chính hệ thống

        Args:
            symbols: Danh sách symbols cần kiểm tra

        Returns:
            Dict mapping symbol -> data (None nếu không có data)
        """
        result = {}

        if not self.api_check_url:
            logger.warning("API check URL not configured")
            return result

        try:
            symbols_str = ",".join(symbols)
            url = f"{self.api_check_url}/crypto/funding_rate_realtime/{symbols_str}"

            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        api_data = data.get("data", [])

                        for item in api_data:
                            symbol = item.get("symbol")
                            if symbol:
                                result[symbol] = item
                    else:
                        logger.error(f"API check failed: {response.status}")

        except asyncio.TimeoutError:
            logger.error("API check timeout")
        except Exception as e:
            logger.error(f"Error checking API: {str(e)}")

        return result

    async def _check_database_data(
        self, symbols: List[str], expected_date: str, expected_time: str
    ) -> Dict[str, bool]:
        """
        Kiểm tra data trong database

        Args:
            symbols: Danh sách symbols
            expected_date: Ngày dự kiến (YYYY-MM-DD)
            expected_time: Thời gian dự kiến (HH:MM:SS)

        Returns:
            Dict mapping symbol -> has_data (True/False)
        """
        result = {}

        try:
            # Sử dụng service hiện có để lấy realtime data
            from src.dto.funding_rate_dto import RealtimeFundingRateRequest

            symbols_str = ",".join(symbols)
            request = RealtimeFundingRateRequest(symbols=symbols_str)
            response = await self.funding_service.get_realtime_funding_rate_data(
                request
            )

            # Khởi tạo tất cả symbols là False
            for symbol in symbols:
                result[symbol] = False

            # Kiểm tra từng data item
            for item in response.data:
                symbol = item.symbol
                update_date = item.update_date
                update_time = item.update_time

                # Kiểm tra xem data có đủ mới không
                if update_date == expected_date:
                    # Parse time để so sánh
                    try:
                        update_datetime = datetime.strptime(
                            f"{update_date} {update_time}", "%Y-%m-%d %H:%M:%S"
                        )
                        expected_datetime = datetime.strptime(
                            f"{expected_date} {expected_time}", "%Y-%m-%d %H:%M:%S"
                        )

                        # Cho phép tolerance
                        time_diff = abs(
                            (update_datetime - expected_datetime).total_seconds()
                        )
                        if time_diff <= self.tolerance_minutes * 60:
                            result[symbol] = True
                    except ValueError:
                        logger.warning(
                            f"Cannot parse time for {symbol}: {update_date} {update_time}"
                        )

        except Exception as e:
            logger.error(f"Error checking database: {str(e)}")

        return result

    async def check_funding_rate_data(self) -> Dict[str, any]:
        """
        Check funding rate data and send alert if needed
        Only checks and alerts if we're within tolerance window of a funding time

        Returns:
            Dict containing check results
        """
        logger.info("Starting funding rate data check...")

        expected_date, expected_time, should_check = (
            self._get_current_funding_schedule()
        )
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        result = {
            "timestamp": current_time,
            "expected_date": expected_date,
            "expected_time": expected_time,
            "should_check": should_check,
            "symbols_checked": self.expected_symbols,
            "missing_symbols": [],
            "api_check_result": {},
            "database_check_result": {},
            "alert_sent": False,
            "status": "OK",
        }

        # Only perform actual checks if we're in a check window
        if not should_check:
            result["status"] = "NO_CHECK_NEEDED"
            logger.info(
                f"Not in funding rate check window. Next funding time: {expected_date} {expected_time}"
            )
            return result

        try:
            # Check API data
            api_data = await self._check_api_data(self.expected_symbols)
            result["api_check_result"] = api_data

            # Check database data
            db_data = await self._check_database_data(
                self.expected_symbols, expected_date, expected_time
            )
            result["database_check_result"] = db_data

            # Find symbols missing data
            missing_symbols = []
            for symbol in self.expected_symbols:
                has_api_data = symbol in api_data
                has_db_data = db_data.get(symbol, False)

                if not has_api_data or not has_db_data:
                    missing_symbols.append(symbol)

            result["missing_symbols"] = missing_symbols

            # Send alert if symbols missing data
            if missing_symbols:
                result["status"] = "WARNING"
                alert_sent = await self.telegram_service.send_funding_rate_alert(
                    missing_symbols, f"{expected_date} {expected_time}"
                )
                result["alert_sent"] = alert_sent

                logger.warning(
                    f"Detected {len(missing_symbols)} symbols missing data: {missing_symbols}"
                )
            else:
                logger.info("All symbols have complete data")

        except Exception as e:
            logger.error(f"Error during check process: {str(e)}")
            result["status"] = "ERROR"
            result["error"] = str(e)

            # Gửi thông báo lỗi
            await self.telegram_service.send_system_status(
                "ERROR", f"Error checking funding rate data: {str(e)}"
            )

        return result

    async def get_monitoring_status(self) -> Dict[str, any]:
        """
        Get current monitoring status

        Returns:
            Dict containing status information
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        expected_date, expected_time, should_check = (
            self._get_current_funding_schedule()
        )

        return {
            "timestamp": current_time,
            "service_status": "RUNNING",
            "expected_symbols": self.expected_symbols,
            "next_expected_funding_time": f"{expected_date} {expected_time}",
            "in_check_window": should_check,
            "tolerance_minutes": self.tolerance_minutes,
            "api_check_url": self.api_check_url,
            "telegram_configured": bool(
                self.telegram_service.bot_token and self.telegram_service.chat_id
            ),
        }


def get_funding_rate_monitor_service() -> FundingRateMonitorService:
    """Dependency injection cho FundingRateMonitorService"""
    return FundingRateMonitorService()
