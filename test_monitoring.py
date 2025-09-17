#!/usr/bin/env python3
"""
Script to test monitoring system manually
"""
import asyncio
import sys
import os

# Add root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.service.monitoring_service import get_funding_rate_monitor_service
from src.service.telegram_service import get_telegram_service
from src.config.logger_config import logger


async def test_telegram():
    """Test sending Telegram messages"""
    print("=== Test Telegram Service ===")
    telegram_service = get_telegram_service()

    # Test simple message
    success = await telegram_service.send_message("Test message from Monitoring System")
    print(f"Send test message: {'✅ Success' if success else '❌ Failed'}")

    # Test funding rate alert
    test_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
    success = await telegram_service.send_funding_rate_alert(
        test_symbols, "2025-09-18 08:00:00"
    )
    print(f"Send funding rate alert: {'✅ Success' if success else '❌ Failed'}")

    # Test system status
    success = await telegram_service.send_system_status(
        "OK", "System operating normally"
    )
    print(f"Send system status: {'✅ Success' if success else '❌ Failed'}")


async def test_monitoring():
    """Test monitoring service"""
    print("\n=== Test Monitoring Service ===")
    monitoring_service = get_funding_rate_monitor_service()

    # Test get status
    status = await monitoring_service.get_monitoring_status()
    print("Monitoring status:")
    for key, value in status.items():
        print(f"  {key}: {value}")

    # Test data check
    print("\nStarting funding rate data check...")
    result = await monitoring_service.check_funding_rate_data()
    print("Check results:")
    for key, value in result.items():
        if key not in ["api_check_result", "database_check_result"]:
            print(f"  {key}: {value}")

    if result.get("missing_symbols"):
        print(f"⚠️  Symbols missing data: {result['missing_symbols']}")
    else:
        print("✅ All symbols have data")


async def main():
    """Main function"""
    print("🚀 Starting Monitoring System Test\n")

    try:
        # Test Telegram
        await test_telegram()

        # Test Monitoring
        await test_monitoring()

        print("\n✅ Test completed!")

    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
