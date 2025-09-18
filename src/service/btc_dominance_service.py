import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
from src.config.mongo_config import MongoDBConfig, get_db_and_collections_btcdominance
from src.dto.btc_dominance_dto import BTCDominanceRequest, BTCDominanceResponse, RealtimeBTCDominanceRequest, RealtimeBTCDominanceResponse
from src.model.btc_dominance import BTCDominanceModel, RealtimeBTCDominanceModel


class BTCDominanceService:
    def __init__(self, db_client=None):
        self._client = db_client or MongoDBConfig().get_client()  # Đảm bảo có () để tạo instance
        self._db_name, self._realtime_col, self._history_col = get_db_and_collections_btcdominance()
        self._logger = logging.getLogger(__name__)

    async def get_historical_btc_dominance_data(self, request: BTCDominanceRequest) -> BTCDominanceResponse:
        days = request.days
        if days <= 0:
            return BTCDominanceResponse(data=[])  # Trả về rỗng nếu days không hợp lệ
        
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
            self._logger.debug("Querying DB=%s Collection=%s start=%s end=%s start_ms=%d end_ms=%d", self._db_name, self._history_col, start_date_dt.isoformat(), end_date_dt.isoformat(), start_ms, end_ms)
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
                    {"$project": {"_id": 1, "timestamp_ms": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "datetime": 1}},
                ]
                return list(col.aggregate(pipeline))
            except Exception:
                # Fallback to numeric find (works when timestamp_ms stored as number)
                projection = {"_id": 1, "timestamp_ms": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "datetime": 1}
                cursor = col.find({"timestamp_ms": {"$gte": start_ms, "$lte": end_ms}}, projection).sort([("timestamp_ms", -1)])
                return list(cursor)

        # Second try: use $dateFromString to parse `datetime` strings with format "%Y-%m-%d %H:%M:%S"
        def _query_by_datefromstring():
            pipeline = [
                {
                    "$match": {
                        "$expr": {
                            "$and": [
                                {"$gte": [{"$dateFromString": {"dateString": "$datetime", "format": "%Y-%m-%d %H:%M:%S"}}, start_date_dt]},
                                {"$lte": [{"$dateFromString": {"dateString": "$datetime", "format": "%Y-%m-%d %H:%M:%S"}}, end_date_dt]},
                            ]
                        }
                    }
                },
                {"$sort": {"timestamp_ms": -1, "datetime": -1}},
                {"$project": {"_id": 1, "timestamp_ms": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "datetime": 1}},
            ]
            return list(col.aggregate(pipeline))

        # Third fallback: try original $toDate approach (may work for ISO strings)
        def _fallback_query():
            pipeline2 = [
                {"$match": {"datetime": {"$gte": start_date_dt, "$lte": end_date_dt}}},
                {"$sort": {"datetime": -1}},
                {"$project": {"_id": 1, "timestamp_ms": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "datetime": 1}},
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
                projection = {"_id": 1, "timestamp_ms": 1, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "datetime": 1}
                cursor = col.find({"datetime": {"$gte": start_str, "$lte": end_str}}, projection).sort([("datetime", -1)])
                return list(cursor)

            docs = await loop.run_in_executor(None, _query_by_datetime_string)

        if not docs:
            docs = await loop.run_in_executor(None, _fallback_query)

        # Ghi log để debug vì user báo không có dữ liệu
        try:
            self._logger.info("BTC dominance historical query returned %d documents", len(docs))
            if len(docs) > 0:
                sample = docs[0]
                # Log small sample of fields to help debugging
                sample_preview = {k: sample.get(k) for k in ("_id", "timestamp_ms", "datetime", "close")}
                self._logger.debug("Sample doc preview: %s", sample_preview)
        except Exception:
            pass
        # If still empty, log collection count and one sample doc to help debugging
        if not docs:
            try:
                total = col.count_documents({})
                sample_doc = col.find_one()
                self._logger.debug("Collection %s total documents=%d", self._history_col, total)
                if sample_doc:
                    preview = {k: sample_doc.get(k) for k in ("_id", "timestamp_ms", "datetime", "close")}
                    self._logger.debug("Collection sample doc preview: %s", preview)
            except Exception as e:
                self._logger.debug("Could not get collection stats/sample: %s", str(e))
        
        # Chuyển đổi thành các model BTCDominanceModel
        data: List[Dict[str, Any]] = []
        for doc in docs:
            # Keep _id if present; map timestamp_ms and parse datetime if needed
            # Do not remove _id; Pydantic model accepts optional _id
            if isinstance(doc.get('datetime'), str):
                try:
                    # Expecting format "YYYY-MM-DD HH:MM:SS"
                    doc['datetime'] = datetime.strptime(doc['datetime'], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    try:
                        doc['datetime'] = datetime.fromisoformat(doc['datetime'].replace('Z', '+00:00'))
                    except Exception:
                        doc.pop('datetime', None)

            # Ensure numeric fields exist and convert if necessary
            for fld in ('open', 'high', 'low', 'close'):
                if fld in doc:
                    try:
                        doc[fld] = float(doc[fld])
                    except Exception:
                        doc[fld] = None

            # timestamp_ms may be int or string in DB
            if 'timestamp_ms' in doc:
                try:
                    doc['timestamp_ms'] = int(doc['timestamp_ms'])
                except Exception:
                    doc['timestamp_ms'] = None

            btc_dominance = BTCDominanceModel(**doc)
            data.append(btc_dominance.model_dump())
        
        return BTCDominanceResponse(data=data)

    async def get_realtime_btc_dominance_data(self, request: RealtimeBTCDominanceRequest) -> RealtimeBTCDominanceResponse:
        db = self._client[self._db_name]
        # realtime uses the same raw collection and we pick the latest by timestamp_ms
        col = db[self._realtime_col]
        
        loop = asyncio.get_running_loop()
        
        def _query():
            # Prefer sorting by timestamp_ms if available, fallback to datetime
            try:
                doc = col.find_one(sort=[("timestamp_ms", -1)])
                if doc:
                    return doc
            except Exception:
                # some mongodb servers or drivers may error if field missing or index missing
                pass

            # Fallback: try sorting by datetime field
            try:
                doc = col.find_one(sort=[("datetime", -1)])
                return doc
            except Exception:
                return None
        
        doc = await loop.run_in_executor(None, _query)

        if doc:
            # Map and parse similar to historical
            try:
                self._logger.debug("Realtime doc found keys: %s", list(doc.keys()))
            except Exception:
                pass
            if isinstance(doc.get('datetime'), str):
                try:
                    doc['datetime'] = datetime.strptime(doc['datetime'], "%Y-%m-%d %H:%M:%S")
                except Exception:
                    try:
                        doc['datetime'] = datetime.fromisoformat(doc['datetime'].replace('Z', '+00:00'))
                    except Exception:
                        doc.pop('datetime', None)

            for fld in ('open', 'high', 'low', 'close'):
                if fld in doc:
                    try:
                        doc[fld] = float(doc[fld])
                    except Exception:
                        doc[fld] = None

            if 'timestamp_ms' in doc:
                try:
                    doc['timestamp_ms'] = int(doc['timestamp_ms'])
                except Exception:
                    doc['timestamp_ms'] = None

            realtime_data = RealtimeBTCDominanceModel(**doc)
            return RealtimeBTCDominanceResponse(data=[realtime_data.model_dump()])
        else:
            # Log collection status to help debugging if realtime not found
            try:
                total = col.count_documents({})
                sample_doc = col.find_one()
                self._logger.debug("Realtime collection %s total documents=%d", self._realtime_col, total)
                if sample_doc:
                    preview = {k: sample_doc.get(k) for k in ("_id", "timestamp_ms", "datetime", "close")}
                    self._logger.debug("Realtime collection sample: %s", preview)
            except Exception as e:
                self._logger.debug("Could not get realtime collection stats/sample: %s", str(e))

            return RealtimeBTCDominanceResponse(data=[])


def get_btc_dominance_service():
    return BTCDominanceService()






