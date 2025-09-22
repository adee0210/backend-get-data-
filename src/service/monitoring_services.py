import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from src.config.variable_config import MONITORING_CONFIG
from src.config.logger_config import logger
from src.service.funding_rate_service import (
    FundingRateService,
    get_funding_rate_service,
)
from src.service.btc_dominance_service import (
    BTCDominanceService,
    get_btc_dominance_service,
)
from src.dto.funding_rate_dto import RealtimeFundingRateRequest
from src.dto.btc_dominance_dto import RealtimeBTCDominanceRequest


class FundingRateMonitoringService:
    """Service để check funding rate theo các chu kỳ 8h, 4h, 1h"""

    def __init__(self, funding_service: FundingRateService = None):
        self.funding_service = funding_service or get_funding_rate_service()
        self.expected_symbols = MONITORING_CONFIG.get("expected_symbols", [])
        self.tolerance_minutes = MONITORING_CONFIG.get("tolerance_minutes", 30)

    def _get_funding_cycles(self) -> Dict[str, List[str]]:
        """Get funding rate cycles"""
        return {
            "8h": ["00:00:00", "08:00:00", "16:00:00"],
            "4h": ["00:00:00", "04:00:00", "08:00:00", "12:00:00", "16:00:00", "20:00:00"],
            "1h": [f"{hour:02d}:00:00" for hour in range(24)]
        }

    def _get_current_funding_schedule(self, cycle_type: str) -> Tuple[str, str, bool, str]:
        """Get current funding schedule for specific cycle and check if we should alert"""
        now = datetime.now()
        funding_times = self._get_funding_cycles()[cycle_type]
        today = now.strftime("%Y-%m-%d")

        # Check if we're within tolerance of any funding time today
        for time_str in funding_times:
            expected_datetime = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M:%S")
            
            if expected_datetime <= now <= expected_datetime + timedelta(minutes=self.tolerance_minutes):
                return today, time_str, True, "current"

        # Find next funding time
        for time_str in funding_times:
            expected_datetime = datetime.strptime(f"{today} {time_str}", "%Y-%m-%d %H:%M:%S")
            if now < expected_datetime:
                return today, time_str, False, "upcoming"

        # Next day first time
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        return tomorrow, funding_times[0], False, "next_day"

    async def _check_funding_rate_data(self, symbols: List[str], expected_date: str, expected_time: str) -> Dict[str, any]:
        """Check funding rate data from database"""
        result = {}

        try:
            symbols_str = ",".join(symbols)
            request = RealtimeFundingRateRequest(symbols=symbols_str)
            response = await self.funding_service.get_realtime_funding_rate_data(request)

            # Initialize all symbols as False
            for symbol in symbols:
                result[symbol] = {"has_data": False, "latest_record": None}

            # Check each data item
            for item in response.data:
                symbol = item.symbol
                update_date = item.update_date
                update_time = item.update_time

                latest_record = {
                    "symbol": symbol,
                    "funding_rate": item.funding_rate,
                    "update_date": update_date,
                    "update_time": update_time
                }

                if update_date == expected_date:
                    try:
                        update_datetime = datetime.strptime(f"{update_date} {update_time}", "%Y-%m-%d %H:%M:%S")
                        expected_datetime = datetime.strptime(f"{expected_date} {expected_time}", "%Y-%m-%d %H:%M:%S")

                        time_diff = abs((update_datetime - expected_datetime).total_seconds())
                        if time_diff <= self.tolerance_minutes * 60:
                            result[symbol] = {
                                "has_data": True,
                                "latest_record": latest_record
                            }
                        else:
                            result[symbol] = {
                                "has_data": False,
                                "latest_record": {**latest_record, "time_diff_minutes": round(time_diff / 60, 2)}
                            }
                    except ValueError:
                        logger.warning(f"Cannot parse time for {symbol}: {update_date} {update_time}")
                        result[symbol] = {"has_data": False, "latest_record": latest_record}
                else:
                    result[symbol] = {"has_data": False, "latest_record": latest_record}

        except Exception as e:
            logger.error(f"Error checking funding rate data: {str(e)}")

        return result

    async def check_funding_rate(self) -> Dict[str, any]:
        """Check funding rate data according to multiple cycles (8h, 4h, 1h)"""
        logger.info("Checking funding rate data for all cycles...")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cycles = ["8h", "4h", "1h"]
        
        result = {
            "timestamp": current_time,
            "cycles": {},
            "overall_status": "OK",
            "overall_alert_message": "",
            "total_symbols": len(self.expected_symbols)
        }

        try:
            for cycle in cycles:
                expected_date, expected_time, should_check, schedule_status = self._get_current_funding_schedule(cycle)
                
                cycle_result = {
                    "expected_funding_time": f"{expected_date} {expected_time}",
                    "is_funding_time": should_check,
                    "schedule_status": schedule_status,
                    "symbols_with_data": 0,
                    "symbols_missing_data": 0,
                    "missing_symbols": [],
                    "symbols_details": {},
                    "status": "OK",
                    "alert_message": ""
                }

                if should_check:
                    # Check funding rate data for this cycle
                    symbols_data = await self._check_funding_rate_data(self.expected_symbols, expected_date, expected_time)
                    cycle_result["symbols_details"] = symbols_data

                    # Count symbols with/without data
                    missing_symbols = []
                    for symbol in self.expected_symbols:
                        symbol_info = symbols_data.get(symbol, {"has_data": False})
                        if symbol_info["has_data"]:
                            cycle_result["symbols_with_data"] += 1
                        else:
                            cycle_result["symbols_missing_data"] += 1
                            missing_symbols.append(symbol)

                    cycle_result["missing_symbols"] = missing_symbols

                    if missing_symbols:
                        cycle_result["status"] = "WARNING"
                        cycle_result["alert_message"] = f"FUNDING RATE {cycle.upper()} ALERT: {len(missing_symbols)} symbols missing data at {expected_date} {expected_time}: {', '.join(missing_symbols)}"
                        logger.warning(cycle_result["alert_message"])
                        
                        # Update overall status
                        if result["overall_status"] == "OK":
                            result["overall_status"] = "WARNING"
                    else:
                        cycle_result["alert_message"] = f"All {len(self.expected_symbols)} symbols have funding rate data for {cycle} cycle"
                        logger.info(f"All funding rate symbols have complete data for {cycle} cycle")
                else:
                    cycle_result["status"] = "NO_CHECK_NEEDED"
                    cycle_result["alert_message"] = f"Not in {cycle} funding rate check window. Next funding time: {expected_date} {expected_time}"

                result["cycles"][cycle] = cycle_result

            # Set overall alert message
            warnings = []
            for cycle, cycle_data in result["cycles"].items():
                if cycle_data["status"] == "WARNING":
                    warnings.append(f"{cycle}: {cycle_data['symbols_missing_data']} symbols missing")
            
            if warnings:
                result["overall_alert_message"] = f"FUNDING RATE ALERTS - {', '.join(warnings)}"
            else:
                active_cycles = [cycle for cycle, data in result["cycles"].items() if data["is_funding_time"]]
                if active_cycles:
                    result["overall_alert_message"] = f"All symbols have complete data for active cycles: {', '.join(active_cycles)}"
                else:
                    result["overall_alert_message"] = "No active funding rate checks at this time"

        except Exception as e:
            logger.error(f"Error during funding rate check: {str(e)}")
            result["overall_status"] = "ERROR"
            result["overall_alert_message"] = f"Error checking funding rate data: {str(e)}"

        return result


class BTCDominanceMonitoringService:
    """Service để check BTC dominance có data trong ngày hôm nay"""

    def __init__(self, btc_service: BTCDominanceService = None):
        self.btc_service = btc_service or get_btc_dominance_service()

    async def check_btc_dominance(self) -> Dict[str, any]:
        """Check BTC dominance có data trong ngày hôm nay không"""
        logger.info("Checking BTC dominance data for today...")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().strftime("%Y-%m-%d")

        result = {
            "timestamp": current_time,
            "check_date": today,
            "has_today_data": False,
            "latest_record": None,
            "records_count_today": 0,
            "alert_message": "",
            "status": "OK"
        }

        try:
            # Get realtime BTC dominance data (type: realtime)
            request = RealtimeBTCDominanceRequest()
            response = await self.btc_service.get_realtime_btc_dominance_data(request)

            if response.data and len(response.data) > 0:
                # Filter records for today with type: realtime
                today_records = []
                latest_realtime_record = None
                
                for record in response.data:
                    # Check if record has type: realtime
                    if record.get("type") == "realtime":
                        # Remove type field from record for output
                        clean_record = {k: v for k, v in record.items() if k != "type"}
                        
                        # Check if record is from today
                        if clean_record.get("datetime"):
                            try:
                                if isinstance(clean_record["datetime"], str):
                                    record_date = clean_record["datetime"][:10]  # Get YYYY-MM-DD part
                                else:
                                    record_date = clean_record["datetime"].strftime("%Y-%m-%d")
                                
                                if record_date == today:
                                    today_records.append(clean_record)
                                
                                # Keep track of latest realtime record overall
                                if latest_realtime_record is None:
                                    latest_realtime_record = clean_record

                            except Exception as e:
                                logger.warning(f"Cannot parse datetime from realtime record: {str(e)}")

                result["latest_record"] = latest_realtime_record
                result["records_count_today"] = len(today_records)

                if today_records:
                    result["has_today_data"] = True
                    result["status"] = "OK"
                    result["alert_message"] = f"BTC dominance has {len(today_records)} realtime records for today ({today})"
                    logger.info(f"Found {len(today_records)} BTC dominance realtime records for today")
                else:
                    result["status"] = "WARNING"
                    result["alert_message"] = f"BTC DOMINANCE ALERT: No realtime data found for today ({today})"
                    logger.warning(result["alert_message"])
            else:
                result["status"] = "ERROR"
                result["alert_message"] = "BTC DOMINANCE ALERT: No realtime data found in database"
                logger.error(result["alert_message"])

        except Exception as e:
            logger.error(f"Error checking BTC dominance: {str(e)}")
            result["status"] = "ERROR"
            result["alert_message"] = f"Error checking BTC dominance data: {str(e)}"

        return result


# Global service instances
_funding_rate_monitor = None
_btc_dominance_monitor = None


def get_funding_rate_monitoring_service() -> FundingRateMonitoringService:
    """Singleton for FundingRateMonitoringService"""
    global _funding_rate_monitor
    if _funding_rate_monitor is None:
        _funding_rate_monitor = FundingRateMonitoringService()
    return _funding_rate_monitor


def get_btc_dominance_monitoring_service() -> BTCDominanceMonitoringService:
    """Singleton for BTCDominanceMonitoringService"""
    global _btc_dominance_monitor
    if _btc_dominance_monitor is None:
        _btc_dominance_monitor = BTCDominanceMonitoringService()
    return _btc_dominance_monitor