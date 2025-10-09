import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging
from src.config.logger_config import logger
from src.config.mongo_config import MongoDBConfig, get_db_and_collections_btcdominance
from src.dto.btc_dominance_dto import (
    BTCDominanceRequest,
    BTCDominanceResponse,
    RealtimeBTCDominanceRequest,
    RealtimeBTCDominanceResponse,
)
from src.model.btc_dominance import BTCDominanceModel, RealtimeBTCDominanceModel


class BTCDominanceService:
    def __init__(self, db_client=None):
        self._client = (
            db_client or MongoDBConfig().get_client()
        )  # Đảm bảo có () để tạo instance
        self._db_name, self._realtime_col, self._history_col = (
            get_db_and_collections_btcdominance()
        )
        self._logger = logging.getLogger(__name__)

    async def get_btc_dominance_data(
        self, request: BTCDominanceRequest
    ) -> BTCDominanceResponse:
        """Get BTC dominance data - historical or latest records"""
        days = request.days
        from_date = request.from_date
        to_date = request.to_date

        # Nếu có from_date và to_date, sử dụng date range query
        if from_date and to_date:
            return await self._get_data_by_date_range(from_date, to_date, days)

        # Nếu chỉ có days hoặc không có gì cả
        if days is None:
            days = 1  # Default value

        if days == 0:
            # day=0 means realtime (latest records)
            return await self._get_latest_records()
        elif days < 0:
            return BTCDominanceResponse(data=[])

        # Historical data query
        return await self._get_historical_data(days)

    async def _get_historical_data(self, days: int) -> BTCDominanceResponse:
        """Get historical BTC dominance data"""
        if not self._db_name or not self._history_col:
            logger.error("Database or collection name not configured")
            return BTCDominanceResponse(data=[])

        db = self._client[self._db_name]
        # history collection is the same raw collection
        col = db[self._history_col]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        # Prefer querying by actual datetime objects for efficiency and index use
        start_date_dt = start_date
        end_date_dt = end_date

        loop = asyncio.get_running_loop()

        # First try: query by timestamp_ms range (most robust when data stores ms)
        start_ms = int(start_date_dt.timestamp() * 1000)
        end_ms = int(end_date_dt.timestamp() * 1000)
        # Debug: log db/collection and computed ranges
        try:
            self._logger.debug(
                "Querying DB=%s Collection=%s start=%s end=%s start_ms=%d end_ms=%d",
                self._db_name,
                self._history_col,
                start_date_dt.isoformat(),
                end_date_dt.isoformat(),
                start_ms,
                end_ms,
            )
        except Exception:
            pass

        def _query_by_timestamp_ms():
            # Prefer aggregation that converts timestamp_ms to long (handles numeric or string stored values)
            try:
                pipeline = [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$gte": [{"$toLong": "$timestamp_ms"}, start_ms]},
                                    {"$lte": [{"$toLong": "$timestamp_ms"}, end_ms]},
                                ]
                            }
                        }
                    },
                    {"$sort": {"timestamp_ms": -1}},
                    {
                        "$project": {
                            "_id": 1,
                            "timestamp_ms": 1,
                            "open": 1,
                            "high": 1,
                            "low": 1,
                            "close": 1,
                            "volume": 1,
                            "datetime": 1,
                        }
                    },
                ]
                return list(col.aggregate(pipeline))
            except Exception:
                # Fallback to numeric find (works when timestamp_ms stored as number)
                projection = {
                    "_id": 1,
                    "timestamp_ms": 1,
                    "open": 1,
                    "high": 1,
                    "low": 1,
                    "close": 1,
                    "volume": 1,
                    "datetime": 1,
                }
                cursor = col.find(
                    {"timestamp_ms": {"$gte": start_ms, "$lte": end_ms}}, projection
                ).sort([("timestamp_ms", -1)])
                return list(cursor)

        # Second try: use $dateFromString to parse `datetime` strings with format "%Y-%m-%d %H:%M:%S"
        def _query_by_datefromstring():
            pipeline = [
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {
                                    "$gte": [
                                        {
                                            "$dateFromString": {
                                                "dateString": "$datetime",
                                                "format": "%Y-%m-%d %H:%M:%S",
                                            }
                                        },
                                        start_date_dt,
                                    ]
                                },
                                {
                                    "$lte": [
                                        {
                                            "$dateFromString": {
                                                "dateString": "$datetime",
                                                "format": "%Y-%m-%d %H:%M:%S",
                                            }
                                        },
                                        end_date_dt,
                                    ]
                                },
                            ]
                        }
                    }
                },
                {"$sort": {"timestamp_ms": -1, "datetime": -1}},
                {
                    "$project": {
                        "_id": 1,
                        "timestamp_ms": 1,
                        "open": 1,
                        "high": 1,
                        "low": 1,
                        "close": 1,
                        "volume": 1,
                        "datetime": 1,
                    }
                },
            ]
            return list(col.aggregate(pipeline))

        # Third fallback: try original $toDate approach (may work for ISO strings)
        def _fallback_query():
            pipeline2 = [
                {"$match": {"datetime": {"$gte": start_date_dt, "$lte": end_date_dt}}},
                {"$sort": {"datetime": -1}},
                {
                    "$project": {
                        "_id": 1,
                        "timestamp_ms": 1,
                        "open": 1,
                        "high": 1,
                        "low": 1,
                        "close": 1,
                        "volume": 1,
                        "datetime": 1,
                    }
                },
            ]
            return list(col.aggregate(pipeline2))

        # Try queries in order: timestamp_ms -> dateFromString -> fallback
        docs = await loop.run_in_executor(None, _query_by_timestamp_ms)
        if not docs:
            docs = await loop.run_in_executor(None, _query_by_datefromstring)

        # If still empty, try matching datetime stored as plain string range
        if not docs:

            def _query_by_datetime_string():
                start_str = start_date_dt.strftime("%Y-%m-%d %H:%M:%S")
                end_str = end_date_dt.strftime("%Y-%m-%d %H:%M:%S")
                projection = {
                    "_id": 1,
                    "timestamp_ms": 1,
                    "open": 1,
                    "high": 1,
                    "low": 1,
                    "close": 1,
                    "volume": 1,
                    "datetime": 1,
                }
                cursor = col.find(
                    {"datetime": {"$gte": start_str, "$lte": end_str}}, projection
                ).sort([("datetime", -1)])
                return list(cursor)

            docs = await loop.run_in_executor(None, _query_by_datetime_string)

        if not docs:
            docs = await loop.run_in_executor(None, _fallback_query)

        # Ghi log để debug vì user báo không có dữ liệu
        try:
            self._logger.info(
                "BTC dominance historical query returned %d documents", len(docs)
            )
            if len(docs) > 0:
                sample = docs[0]
                # Log small sample of fields to help debugging
                sample_preview = {
                    k: sample.get(k)
                    for k in ("_id", "timestamp_ms", "datetime", "close")
                }
                self._logger.debug("Sample doc preview: %s", sample_preview)
        except Exception:
            pass
        # If still empty, log collection count and one sample doc to help debugging
        if not docs:
            try:
                total = col.count_documents({})
                sample_doc = col.find_one()
                self._logger.debug(
                    "Collection %s total documents=%d", self._history_col, total
                )
                if sample_doc:
                    preview = {
                        k: sample_doc.get(k)
                        for k in ("_id", "timestamp_ms", "datetime", "close")
                    }
                    self._logger.debug("Collection sample doc preview: %s", preview)
            except Exception as e:
                self._logger.debug("Could not get collection stats/sample: %s", str(e))

        # Chuyển đổi thành các model BTCDominanceModel
        data: List[Dict[str, Any]] = []
        for doc in docs:
            # Keep _id if present; map timestamp_ms and parse datetime if needed
            # Do not remove _id; Pydantic model accepts optional _id
            if isinstance(doc.get("datetime"), str):
                try:
                    # Parse datetime and convert to date only (YYYY-MM-DD)
                    dt_obj = datetime.strptime(doc["datetime"], "%Y-%m-%d %H:%M:%S")
                    doc["datetime"] = dt_obj.strftime("%Y-%m-%d")
                except Exception:
                    try:
                        dt_obj = datetime.fromisoformat(
                            doc["datetime"].replace("Z", "+00:00")
                        )
                        doc["datetime"] = dt_obj.strftime("%Y-%m-%d")
                    except Exception:
                        # If can't parse, try to extract YYYY-MM-DD part
                        if len(doc["datetime"]) >= 10:
                            doc["datetime"] = doc["datetime"][:10]
                        else:
                            doc.pop("datetime", None)

            # Ensure numeric fields exist and convert if necessary
            for fld in ("open", "high", "low", "close"):
                if fld in doc:
                    try:
                        doc[fld] = float(doc[fld])
                    except Exception:
                        doc[fld] = None

            # timestamp_ms may be int or string in DB
            if "timestamp_ms" in doc:
                try:
                    doc["timestamp_ms"] = int(doc["timestamp_ms"])
                except Exception:
                    doc["timestamp_ms"] = None

            btc_dominance = BTCDominanceModel(**doc)
            data.append(btc_dominance.model_dump())

        return BTCDominanceResponse(data=data)

    async def _get_data_by_date_range(
        self, from_date: str, to_date: str, days: Optional[int] = None
    ) -> BTCDominanceResponse:
        """Get BTC dominance data by date range"""
        from datetime import datetime, timedelta

        try:
            # Parse dates from DDMMYYYY format
            from_dt = datetime.strptime(from_date, "%d%m%Y")
            to_dt = datetime.strptime(to_date, "%d%m%Y")

            # Nếu có days, tính toán lại from_date dựa trên to_date
            if days is not None:
                calculated_from = to_dt - timedelta(days=days)
                # Sử dụng ngày muộn hơn giữa from_dt và calculated_from
                from_dt = max(from_dt, calculated_from)

            # Set thời gian bắt đầu và kết thúc cho ngày
            start_date = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

            logger.info(f"BTC date range query: {start_date} to {end_date}")

            if not self._db_name or not self._history_col:
                logger.error("Database or collection name not configured")
                return BTCDominanceResponse(data=[])

            db = self._client[self._db_name]
            col = db[self._history_col]

            # Query by date range
            loop = asyncio.get_running_loop()

            def _query():
                try:
                    # Try datetime field first
                    cursor = col.find(
                        {"datetime": {"$gte": start_date, "$lte": end_date}}
                    ).sort("datetime", -1)

                    results = list(cursor)
                    if results:
                        return results

                    # Try timestamp_ms if datetime fails
                    start_ms = int(start_date.timestamp() * 1000)
                    end_ms = int(end_date.timestamp() * 1000)

                    cursor = col.find(
                        {"timestamp_ms": {"$gte": start_ms, "$lte": end_ms}}
                    ).sort("timestamp_ms", -1)

                    return list(cursor)

                except Exception as e:
                    logger.error(f"BTC date range query error: {str(e)}")
                    return []

            raw_data = await loop.run_in_executor(None, _query)
            logger.info(f"Found {len(raw_data)} BTC records in date range")

            # Convert to response format
            data = []
            for doc in raw_data:
                try:
                    if "_id" in doc:
                        doc["_id"] = str(doc["_id"])

                    # Convert datetime to string format if needed
                    if "datetime" in doc and isinstance(doc["datetime"], datetime):
                        doc["datetime"] = doc["datetime"].strftime("%Y-%m-%d")

                    btc_dominance = BTCDominanceModel(**doc)
                    data.append(btc_dominance.model_dump())
                except Exception as e:
                    logger.warning(f"Error parsing BTC item in date range: {str(e)}")
                    continue

            return BTCDominanceResponse(data=data)

        except Exception as e:
            logger.error(f"Error in BTC date range query: {str(e)}")
            return BTCDominanceResponse(data=[])

    async def _get_latest_records(self) -> BTCDominanceResponse:
        """Get latest records for realtime data (day=0)"""
        self._logger.info("Getting latest BTC dominance records")

        try:
            if not self._db_name or not self._history_col:
                logger.error("Database or collection name not configured")
                return BTCDominanceResponse(data=[])

            db = self._client[self._db_name]
            col = db[
                self._history_col
            ]  # Same collection for both historical and latest

            loop = asyncio.get_running_loop()

            def _query_latest():
                # Get latest record sorted by datetime or timestamp_ms
                cursor = (
                    col.find().sort([("datetime", -1), ("timestamp_ms", -1)]).limit(1)
                )
                return list(cursor)

            raw_data = await loop.run_in_executor(None, _query_latest)

            self._logger.info(f"Found {len(raw_data)} latest BTC records")
            if raw_data:
                self._logger.info(f"Sample latest BTC record: {raw_data[0]}")

            # Convert to model objects
            data = []
            for item in raw_data:
                try:
                    # Convert ObjectId to string if present
                    if "_id" in item:
                        item["_id"] = str(item["_id"])

                    # Handle datetime parsing - convert to YYYY-MM-DD format
                    if isinstance(item.get("datetime"), str):
                        try:
                            # Parse datetime and convert to date only (YYYY-MM-DD)
                            dt_obj = datetime.strptime(
                                item["datetime"], "%Y-%m-%d %H:%M:%S"
                            )
                            item["datetime"] = dt_obj.strftime("%Y-%m-%d")
                        except Exception:
                            try:
                                dt_obj = datetime.fromisoformat(
                                    item["datetime"].replace("Z", "+00:00")
                                )
                                item["datetime"] = dt_obj.strftime("%Y-%m-%d")
                            except Exception:
                                # If can't parse, try to extract YYYY-MM-DD part
                                if len(item["datetime"]) >= 10:
                                    item["datetime"] = item["datetime"][:10]
                                else:
                                    item.pop("datetime", None)

                    # Handle numeric fields
                    for fld in ("open", "high", "low", "close", "volume"):
                        if fld in item:
                            try:
                                item[fld] = float(item[fld])
                            except Exception:
                                item[fld] = None

                    if "timestamp_ms" in item:
                        try:
                            item["timestamp_ms"] = int(item["timestamp_ms"])
                        except Exception:
                            item["timestamp_ms"] = None

                    btc_model = BTCDominanceModel(**item)
                    data.append(btc_model.model_dump())
                    self._logger.info(f"Successfully parsed latest BTC item")
                except Exception as e:
                    self._logger.error(
                        f"Error parsing latest BTC item: {str(e)}, item: {item}"
                    )
                    continue

            return BTCDominanceResponse(data=data)

        except Exception as e:
            self._logger.error(f"Error getting latest BTC records: {str(e)}")
            return BTCDominanceResponse(data=[])


def get_btc_dominance_service():
    return BTCDominanceService()
