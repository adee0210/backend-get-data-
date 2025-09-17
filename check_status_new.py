#!/usr/bin/env python3
"""
Script to check monitoring system status
"""
import asyncio
import aiohttp
import sys
import os
from datetime import datetime

# Add root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.variable_config import MONITORING_CONFIG


async def check_api_status(base_url="http://localhost:8000"):
    """Check API status"""
    endpoints = [
        ("/", "Health Check"),
        ("/health", "Health Detail"),
        ("/crypto/monitoring/funding_rate/status", "Monitoring Status"),
        ("/crypto/funding_rate_realtime/BTCUSDT", "Funding Rate API"),
    ]

    print("🔍 Checking API status...")
    print("=" * 50)

    async with aiohttp.ClientSession() as session:
        for endpoint, name in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        print(f"✅ {name}: OK ({response.status})")
                    else:
                        print(f"⚠️  {name}: {response.status}")
            except asyncio.TimeoutError:
                print(f"⏱️  {name}: Timeout")
            except Exception as e:
                print(f"❌ {name}: Error - {str(e)}")


async def check_monitoring_detail(base_url="http://localhost:8000"):
    """Check monitoring details"""
    print("\n📊 Monitoring System Details...")
    print("=" * 50)

    try:
        async with aiohttp.ClientSession() as session:
            url = f"{base_url}/crypto/monitoring/funding_rate/status"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    print(f"⏰ Timestamp: {data.get('timestamp', 'N/A')}")
                    print(f"🔧 Service Status: {data.get('service_status', 'N/A')}")
                    print(
                        f"📈 Expected Symbols: {', '.join(data.get('expected_symbols', []))}"
                    )
                    print(
                        f"⏳ Next Funding Time: {data.get('next_expected_funding_time', 'N/A')}"
                    )
                    print(
                        f"🕐 Tolerance: {data.get('tolerance_minutes', 'N/A')} minutes"
                    )
                    print(f"🔗 API Check URL: {data.get('api_check_url', 'N/A')}")
                    print(
                        f"📱 Telegram: {'✅ Configured' if data.get('telegram_configured') else '❌ Not configured'}"
                    )
                else:
                    print(f"❌ Cannot get monitoring status: {response.status}")
    except Exception as e:
        print(f"❌ Error checking monitoring: {str(e)}")


async def trigger_check(base_url="http://localhost:8000"):
    """Trigger manual check"""
    print("\n🔧 Triggering manual check...")
    print("=" * 50)

    try:
        async with aiohttp.ClientSession() as session:
            url = f"{base_url}/crypto/monitoring/funding_rate/check"
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                if response.status == 200:
                    data = await response.json()

                    print(f"⏰ Timestamp: {data.get('timestamp', 'N/A')}")
                    print(
                        f"📅 Expected Time: {data.get('expected_date', 'N/A')} {data.get('expected_time', 'N/A')}"
                    )
                    print(f"📊 Status: {data.get('status', 'N/A')}")
                    print(
                        f"🔍 Symbols Checked: {', '.join(data.get('symbols_checked', []))}"
                    )

                    missing = data.get("missing_symbols", [])
                    if missing:
                        print(f"❌ Missing Symbols: {', '.join(missing)}")
                        print(
                            f"📱 Alert Sent: {'✅ Yes' if data.get('alert_sent') else '❌ No'}"
                        )
                    else:
                        print("✅ All symbols have data")
                else:
                    print(f"❌ Cannot trigger check: {response.status}")
    except Exception as e:
        print(f"❌ Error triggering check: {str(e)}")


def show_config():
    """Show current configuration"""
    print("\n⚙️  Monitoring Configuration...")
    print("=" * 50)

    symbols = MONITORING_CONFIG.get("expected_symbols", [])
    interval = MONITORING_CONFIG.get("funding_rate_check_interval", 3600)
    api_url = MONITORING_CONFIG.get("api_check_url", "N/A")
    tolerance = MONITORING_CONFIG.get("tolerance_minutes", 30)

    print(f"🔄 Check Interval: {interval} seconds ({interval//60} minutes)")
    print(f"📈 Monitored Symbols: {', '.join(symbols)}")
    print(f"🔗 API Check URL: {api_url}")
    print(f"🕐 Tolerance: {tolerance} minutes")


async def main():
    """Main function"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"🚀 System Status Check - {current_time}")
    print("=" * 60)

    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

    print(f"🌐 Checking: {base_url}")

    # Show configuration
    show_config()

    # Check API
    await check_api_status(base_url)

    # Check monitoring details
    await check_monitoring_detail(base_url)

    # Ask if want to trigger check
    print("\n" + "=" * 60)
    response = input("🤔 Do you want to trigger a manual check? (y/N): ").lower()

    if response in ["y", "yes"]:
        await trigger_check(base_url)

    print("\n✅ Check completed!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Check stopped!")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
