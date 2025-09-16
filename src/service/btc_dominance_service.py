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
        col = db[self._history_col]
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        # Prefer querying by actual datetime objects for efficiency and index use
        start_date_dt = start_date
        end_date_dt = end_date
        
        loop = asyncio.get_running_loop()
        
        def _query():
            # Dùng projection để chỉ lấy các trường cần thiết (giảm transfer)
            pipeline = [
                {
                    # Dùng $expr + $toDate để so sánh được cả khi field 'datetime' là string ISO hoặc Date
                    "$match": {
                        "$expr": {
                            "$and": [
                                {"$gte": [{"$toDate": "$datetime"}, start_date_dt]},
                                {"$lte": [{"$toDate": "$datetime"}, end_date_dt]},
                            ]
                        }
                    }
                },
                {"$sort": {"datetime": -1}},
                # Nếu collection có rất nhiều bản ghi, client có thể yêu cầu limit;
                # hiện tại không tự giới hạn để trả đủ ngày yêu cầu, nhưng có thể thêm if cần.
                {
                    "$project": {
                        "_id": 0,
                        "open": 1,
                        "high": 1,
                        "low": 1,
                        "close": 1,
                        "volume": 1,
                        "datetime": 1,
                    }
                }
            ]
            return list(col.aggregate(pipeline))
        
        docs = await loop.run_in_executor(None, _query)
        # Ghi log để debug vì user báo không có dữ liệu
        try:
            self._logger.info("BTC dominance historical query returned %d documents", len(docs))
            if len(docs) > 0:
                # log một sample (tránh log toàn bộ list nếu quá lớn)
                sample = docs[0]
                # Convert sample to string safely
                self._logger.debug("Sample doc keys: %s", list(sample.keys()))
        except Exception:
            pass

        # Nếu không có docs, thử fallback: query bằng match đơn giản (trường datetime có thể là bson datetime)
        if not docs:
            def _fallback_query():
                pipeline2 = [
                    {"$match": {"datetime": {"$gte": start_date_dt, "$lte": end_date_dt}}},
                    {"$sort": {"datetime": -1}},
                    {"$project": {"_id": 0, "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1, "datetime": 1}},
                ]
                return list(col.aggregate(pipeline2))

            docs = await loop.run_in_executor(None, _fallback_query)
            try:
                self._logger.info("Fallback query returned %d documents", len(docs))
            except Exception:
                pass
        
        # Chuyển đổi thành các model BTCDominanceModel
        data: List[Dict[str, Any]] = []
        for doc in docs:
            doc.pop('_id', None)
            # Nếu datetime là string (dữ liệu cũ), parse một lần; ưu tiên datetime type trong DB
            if isinstance(doc.get('datetime'), str):
                try:
                    doc['datetime'] = datetime.fromisoformat(doc['datetime'].replace('Z', '+00:00'))
                except Exception:
                    # Nếu parsing thất bại, bỏ trường datetime để tránh lỗi
                    doc.pop('datetime', None)
            # Kiểm soát: tạo model để validate và ngay lập tức dump về dict
            btc_dominance = BTCDominanceModel(**doc)
            data.append(btc_dominance.model_dump())
        
        return BTCDominanceResponse(data=data)

    async def get_realtime_btc_dominance_data(self, request: RealtimeBTCDominanceRequest) -> RealtimeBTCDominanceResponse:
        db = self._client[self._db_name]
        col = db[self._realtime_col]
        
        loop = asyncio.get_running_loop()
        
        def _query():
            # Lấy document mới nhất theo datetime
            doc = col.find_one(sort=[("datetime", -1)])
            return doc
        
        doc = await loop.run_in_executor(None, _query)
        
        if doc:
            doc.pop('_id', None)
            if isinstance(doc.get('datetime'), str):
                try:
                    doc['datetime'] = datetime.fromisoformat(doc['datetime'].replace('Z', '+00:00'))
                except Exception:
                    doc.pop('datetime', None)
            realtime_data = RealtimeBTCDominanceModel(**doc)
            # Trả về dict để khớp với DTO (list of models) – DTO expects model instances but Pydantic v2
            # sẽ accept dicts in list too; keep consistent with historical endpoint
            return RealtimeBTCDominanceResponse(data=[realtime_data.model_dump()])
        else:
            return RealtimeBTCDominanceResponse(data=[])


def get_btc_dominance_service():
    return BTCDominanceService()






