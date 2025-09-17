#!/usr/bin/env python3
"""
Script to manually test funding rate check at specific times
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.service.monitoring_service import get_funding_rate_monitor_service
from src.service.telegram_service import get_telegram_service


async def test_funding_rate_logic():
    """Test funding rate check logic"""
    print("=== Testing Funding Rate Check Logic ===")

    monitoring_service = get_funding_rate_monitor_service()

    # Test current schedule
    expected_date, expected_time, should_check = (
        monitoring_service._get_current_funding_schedule()
    )

    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Expected funding time: {expected_date} {expected_time}")
    print(f"Should check now: {should_check}")
    print(f"Tolerance window: {monitoring_service.tolerance_minutes} minutes")

    # Show funding schedule for today
    print("\n=== Today's Funding Schedule ===")
    funding_times = monitoring_service._get_expected_funding_times()
    today = datetime.now().strftime("%Y-%m-%d")

    for time_str in funding_times:
        funding_datetime = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M:%S")
        tolerance_end = funding_datetime + timedelta(
            minutes=monitoring_service.tolerance_minutes
        )
        print(
            f"Funding time: {time_str} (check window until {tolerance_end.strftime('%H:%M:%S')})"
        )


async def force_funding_check():
    """Force a funding rate check regardless of time"""
    print("\n=== Force Funding Rate Check ===")

    monitoring_service = get_funding_rate_monitor_service()
    result = await monitoring_service.check_funding_rate_data()

    print("Check Results:")
    for key, value in result.items():
        if key not in ["api_check_result", "database_check_result"]:
            print(f"  {key}: {value}")

    if result.get("missing_symbols"):
        print(f"\n⚠️  Missing symbols: {', '.join(result['missing_symbols'])}")
        print(f"Alert sent: {'Yes' if result.get('alert_sent') else 'No'}")
    else:
        print("\n✅ All symbols have data")


async def test_alert_message():
    """Test alert message format"""
    print("\n=== Test Alert Message Format ===")

    telegram_service = get_telegram_service()
    test_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
    expected_time = "2025-09-18 08:00:00"

    print("Testing alert with all monitored symbols...")
    success = await telegram_service.send_funding_rate_alert(
        test_symbols, expected_time
    )
    print(f"Alert sent: {'✅ Success' if success else '❌ Failed'}")


async def main():
    """Main function"""
    print("🚀 Funding Rate Check Test\n")

    try:
        # Test logic
        await test_funding_rate_logic()

        # Ask user what to do
        print("\n" + "=" * 60)
        print("Choose an action:")
        print("1. Force funding rate check")
        print("2. Test alert message")
        print("3. Both")
        print("4. Exit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            await force_funding_check()
        elif choice == "2":
            await test_alert_message()
        elif choice == "3":
            await force_funding_check()
            await test_alert_message()
        elif choice == "4":
            print("Exiting...")
            return
        else:
            print("Invalid choice")
            return

        print("\n✅ Test completed!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
