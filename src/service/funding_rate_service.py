from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.config.mongo_config import MongoDBConfig, get_db_and_collections
from src.dto.funding_rate_dto import FundingRateRequest, FundingRateResponse, RealtimeFundingRateRequest, RealtimeFundingRateResponse
from src.model.funding_rate import RealtimeFundingRate
from concurrent.futures import ThreadPoolExecutor
import asyncio


class FundingRateService:
    def __init__(self, db_client=None):
        self._client = db_client or MongoDBConfig().get_client()
        self._db_name, self._realtime_col, self._history_col = get_db_and_collections()

    async def get_funding_rate_data(
        self, request: FundingRateRequest
    ) -> FundingRateResponse:
        """Fetch funding rate history for the provided symbols and days.

        The documents in the collection are expected to have fields like:
        - `funding_date` (YYYY-MM-DD string)
        - `funding_time` (HH:MM:SS string)
        - `symbol`
        - `fundingRate`
        - `markPrice`

        Behavior:
        - `symbols` is a comma-separated string of symbols.
        - `days` indicates we should return up to `days` most recent distinct
          `funding_date` entries per symbol (by date).
        - Query uses `funding_date` and `symbol` fields rather than a
          `timestamp` datetime field.
        """
        symbols = [s.strip() for s in request.symbols.split(",") if s.strip()]

        loop = asyncio.get_running_loop()

        def _query():
            db = self._client[self._db_name]
            coll = db[self._history_col]

            # First, get the most recent distinct dates
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

            # Now get all documents for these dates and symbols
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

            # Run aggregation
            docs = list(coll.aggregate(main_pipeline))
            return docs

        docs = await loop.run_in_executor(None, _query)

        # Return docs as-is with original fields (_id, funding_time, symbol, funding_date, fundingRate, markPrice)
        # Remove internal fields like _funding_date_obj
        data: List[Dict[str, Any]] = []
        for doc in docs:
            # Create a clean dict with original fields
            clean_doc = {
                "_id": str(doc.get("_id")),  # Convert ObjectId to string
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
        """Fetch realtime funding rate data for the provided symbols.

        Queries the realtime collection for the latest data per symbol.
        """
        symbols = [s.strip() for s in request.symbols.split(",") if s.strip()]

        loop = asyncio.get_running_loop()

        def _query():
            db = self._client[self._db_name]
            coll = db[self._realtime_col]

            # Get the latest document for each symbol
            pipeline = [
                {"$match": {"symbol": {"$in": symbols}}},
                {"$sort": {"update_date": -1, "update_time": -1}},  # Sort by date and time descending
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

        # Convert to RealtimeFundingRate models
        data: List[RealtimeFundingRate] = []
        for doc in docs:
            realtime_rate = RealtimeFundingRate(
                _id=str(doc.get("_id")),
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
    """Dependency provider for FastAPI to inject FundingRateService.

    This mirrors the Spring-style singletons/services pattern.
    """
    return FundingRateService()
