from typing import List, Dict, Any
from datetime import datetime, timedelta
from src.config.mongo_config import MongoDBConfig, get_db_and_collections
from src.dto.funding_rate_dto import FundingRateRequest, FundingRateResponse
from concurrent.futures import ThreadPoolExecutor
import asyncio


class FundingRateService:
    def __init__(self, db_client=None):
        self._client = db_client or MongoDBConfig().get_client()
        self._db_name, _, self._history_col = get_db_and_collections()

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

            # Use aggregation to get the most recent `days` dates per symbol
            pipeline = [
                {"$match": {"symbol": {"$in": symbols}}},
                # Convert funding_date string to date for sorting if needed
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
                # Group by symbol and funding_date to keep one doc per date (first after sort)
                {
                    "$group": {
                        "_id": {"symbol": "$symbol", "funding_date": "$funding_date"},
                        "doc": {"$first": "$$ROOT"},
                    }
                },
                {"$replaceRoot": {"newRoot": "$doc"}},
                {"$sort": {"_funding_date_obj": -1}},
                {"$limit": request.days * len(symbols)},
            ]

            # Run aggregation
            docs = list(coll.aggregate(pipeline))
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


def get_funding_rate_service():
    """Dependency provider for FastAPI to inject FundingRateService.

    This mirrors the Spring-style singletons/services pattern.
    """
    return FundingRateService()
