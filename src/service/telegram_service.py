import requests
import asyncio
from typing import Optional
from datetime import datetime
from src.config.variable_config import TELEGRAM_CONFIG
from src.config.logger_config import logger


class TelegramService:
    """Service để gửi thông báo qua Telegram Bot"""

    def __init__(self):
        self.bot_token = TELEGRAM_CONFIG.get("bot_token")
        self.chat_id = TELEGRAM_CONFIG.get("chat_id")
        self.api_url = TELEGRAM_CONFIG.get("api_url")

        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot token or chat ID not configured")

    async def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Gửi tin nhắn qua Telegram

        Args:
            message: Nội dung tin nhắn
            parse_mode: Định dạng tin nhắn (HTML, Markdown)

        Returns:
            True nếu gửi thành công, False nếu thất bại
        """
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram not fully configured")
            return False

        url = f"{self.api_url}{self.bot_token}/sendMessage"

        payload = {"chat_id": self.chat_id, "text": message, "parse_mode": parse_mode}

        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, lambda: requests.post(url, json=payload, timeout=10)
            )

            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(
                    f"Failed to send Telegram message: {response.status_code} - {response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending Telegram message: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Telegram: {str(e)}")
            return False

    async def send_funding_rate_alert(
        self, missing_symbols: list, expected_time: str
    ) -> bool:
        """
        Send funding rate missing data alert

        Args:
            missing_symbols: List of symbols missing data
            expected_time: Expected time for data

        Returns:
            True if sent successfully
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        symbols_list = "\n".join([f"{symbol}" for symbol in missing_symbols])

        message = f"""FUNDING RATE ALERT

Time: {current_time}
Expected funding time: {expected_time}

Missing data symbols:
{symbols_list}

Status: API does not have latest funding rate data
Action: Please check data collection system

#FundingRate #DataMissing #Alert"""

        return await self.send_message(message.strip())

    async def send_system_status(self, status: str, details: str = "") -> bool:
        """
        Send system status notification

        Args:
            status: Status (OK, WARNING, ERROR)
            details: Additional details

        Returns:
            True if sent successfully
        """
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        message = f"""SYSTEM MONITORING STATUS

Time: {current_time}
Status: {status}

Details:
{details}

#SystemStatus #Monitoring"""

        return await self.send_message(message.strip())


def get_telegram_service() -> TelegramService:
    """Dependency injection cho TelegramService"""
    return TelegramService()
