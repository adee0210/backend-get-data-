from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.config.mongo_config import MongoDBConfig,get_db_and_collections_funding_rate 
from src.dto.funding_rate_dto import FundingRateRequest, FundingRateResponse, RealtimeFundingRateRequest, RealtimeFundingRateResponse
from src.model.funding_rate import RealtimeFundingRate
import asyncio


class FundingRateService:
    def __init__(self, db_client=None):
        self._client = db_client or MongoDBConfig().get_client()
        self._db_name, self._realtime_col, self._history_col = get_db_and_collections_funding_rate()

    async def get_funding_rate_data(
        self, request: FundingRateRequest
    ) -> FundingRateResponse:
        """Lấy dữ liệu lịch sử funding rate cho các symbol và số ngày được cung cấp.

        Các tài liệu trong collection có các trường:
        - `funding_date` (chuỗi YYYY-MM-DD)
        - `funding_time` (chuỗi HH:MM:SS)
        - `symbol`
        - `fundingRate`
        - `markPrice`

        - `symbols` là chuỗi các symbol cách nhau bởi dấu phẩy.
        - `days` chỉ ra số ngày gần nhất để trả về dữ liệu.
        - Query sử dụng các trường `funding_date` và `symbol`.
        """
        symbols = [s.strip() for s in request.symbols.split(",") if s.strip()]

        loop = asyncio.get_running_loop()

        def _query():
            db = self._client[self._db_name]
            coll = db[self._history_col]

            date_pipeline = [
                {"$match": {"symbol": {"$in": symbols}}},
                {
                    "$addFields": {
                        "_funding_date_obj": {
                            "$dateFromString": {
                                "dateString": "$funding_date",
                                "format": "%Y-%m-%d",
                            }
                        }
                    }
                },
                {"$sort": {"_funding_date_obj": -1}},
                {
                    "$group": {
                        "_id": "$funding_date",
                        "date_obj": {"$first": "$_funding_date_obj"}
                    }
                },
                {"$sort": {"date_obj": -1}},
                {"$limit": request.days},
                {"$project": {"_id": 1}}
            ]

            recent_dates = [doc["_id"] for doc in coll.aggregate(date_pipeline)]

            main_pipeline = [
                {"$match": {
                    "symbol": {"$in": symbols},
                    "funding_date": {"$in": recent_dates}
                }},
                {
                    "$addFields": {
                        "_funding_date_obj": {
                            "$dateFromString": {
                                "dateString": "$funding_date",
                                "format": "%Y-%m-%d",
                            }
                        }
                    }
                },
                {"$sort": {"_funding_date_obj": -1, "funding_time": -1}},
            ]

            # Chạy aggregation
            docs = list(coll.aggregate(main_pipeline))
            return docs

        docs = await loop.run_in_executor(None, _query)

        # Trả về docs với các trường gốc (funding_time, symbol, funding_date, fundingRate, markPrice)
        data: List[Dict[str, Any]] = []
        for doc in docs:
            # Tạo dict sạch với các trường gốc
            clean_doc = {
                "funding_time": doc.get("funding_time"),
                "symbol": doc.get("symbol"),
                "funding_date": doc.get("funding_date"),
                "fundingRate": doc.get("fundingRate"),
                "markPrice": doc.get("markPrice"),
            }
            data.append(clean_doc)

        return FundingRateResponse(data=data)

    async def get_realtime_funding_rate_data(
        self, request: RealtimeFundingRateRequest
    ) -> RealtimeFundingRateResponse:
        symbols = [s.strip() for s in request.symbols.split(",") if s.strip()]

        loop = asyncio.get_running_loop()

        def _query():
            db = self._client[self._db_name]
            coll = db[self._realtime_col]

            # Lấy tài liệu mới nhất cho mỗi symbol
            pipeline = [
                {"$match": {"symbol": {"$in": symbols}}},
                {"$sort": {"update_date": -1, "update_time": -1}},  # Sắp xếp theo ngày và giờ giảm dần
                {
                    "$group": {
                        "_id": "$symbol",
                        "doc": {"$first": "$$ROOT"}
                    }
                },
                {"$replaceRoot": {"newRoot": "$doc"}}
            ]

            docs = list(coll.aggregate(pipeline))
            return docs

        docs = await loop.run_in_executor(None, _query)

        # Chuyển đổi thành các model RealtimeFundingRate
        data: List[RealtimeFundingRate] = []
        for doc in docs:
            realtime_rate = RealtimeFundingRate(
                symbol=doc.get("symbol"),
                funding_cap=doc.get("funding_cap"),
                funding_floor=doc.get("funding_floor"),
                funding_hour=doc.get("funding_hour"),
                funding_rate=doc.get("funding_rate"),
                index_price=doc.get("index_price"),
                interest_rate=doc.get("interest_rate"),
                interval=doc.get("interval"),
                mark_price=doc.get("mark_price"),
                update_date=doc.get("update_date"),
                update_time=doc.get("update_time")
            )
            data.append(realtime_rate)

        return RealtimeFundingRateResponse(data=data)


def get_funding_rate_service():
    return FundingRateService()
