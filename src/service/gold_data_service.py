from typing import List
from datetime import datetime, timedelta
import pymongo
from pymongo import MongoClient

from src.config.mongo_config import MongoDBConfig
from src.config.variable_config import DB_GOLD_DATA
from src.dto.gold_data_dto import GoldDataRequest, GoldDataResponse
from src.model.gold_data import GoldDataModel
from src.config.logger_config import logger


class GoldDataService:
    def __init__(self):
        mongo_config = MongoDBConfig()
        self._client = mongo_config.get_client()
        self._db_name = DB_GOLD_DATA.get("database_name")
        self._history_col = DB_GOLD_DATA.get("collection_history_name")

    def _get_collection(self):
        """Get MongoDB collection for gold data"""
        if not self._db_name or not self._history_col:
            raise ValueError("Database or collection name not configured")

        db = self._client[self._db_name]
        return db[self._history_col]

    async def _query_by_date_range(
        self, collection, start_date: datetime, end_date: datetime
    ) -> List:
        """Query gold data by date range"""
        try:
            # Strategy 1: Query by datetime range
            logger.info(
                f"Gold Strategy 1: Querying by datetime range {start_date} to {end_date}"
            )

            cursor = collection.find(
                {"datetime": {"$gte": start_date, "$lte": end_date}}
            ).sort(
                "datetime", -1
            )  # Latest first

            results = list(cursor)
            logger.info(f"Gold Strategy 1: Found {len(results)} records")

            if results:
                return results

            # Strategy 2: Try string-based date comparison if datetime fails
            logger.info(f"Gold Strategy 2: Trying string-based date comparison")

            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            cursor = collection.find(
                {
                    "$expr": {
                        "$and": [
                            {"$gte": [{"$substr": ["$datetime", 0, 10]}, start_str]},
                            {"$lte": [{"$substr": ["$datetime", 0, 10]}, end_str]},
                        ]
                    }
                }
            ).sort("datetime", -1)

            results = list(cursor)
            logger.info(f"Gold Strategy 2: Found {len(results)} records")

            return results

        except Exception as e:
            logger.error(f"Error in Gold date range query: {str(e)}")
            return []

    async def get_gold_data(self, request: GoldDataRequest) -> GoldDataResponse:
        """Get historical gold data"""
        logger.info(f"Getting gold data for {request.day} days")

        if request.day == 0:
            # day=0 means realtime (latest records)
            return await self._get_latest_records()

        try:
            collection = self._get_collection()

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=request.day)

            logger.info(
                f"Gold date range: {start_date.strftime('%Y-%m-%d %H:%M:%S')} to {end_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )

            # Query data using date range strategy
            raw_data = await self._query_by_date_range(collection, start_date, end_date)

            logger.info(f"Found {len(raw_data)} gold records")

            # Convert to model objects
            data = []
            for item in raw_data:
                try:
                    # Convert ObjectId to string if present
                    if "_id" in item:
                        item["_id"] = str(item["_id"])

                    # Convert datetime to string format with minutes
                    if "datetime" in item and isinstance(item["datetime"], datetime):
                        item["datetime"] = item["datetime"].strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                    gold_model = GoldDataModel(**item)
                    data.append(gold_model)
                except Exception as e:
                    logger.warning(f"Error parsing gold item: {str(e)}, item: {item}")
                    continue

            logger.info(f"Successfully processed {len(data)} gold records")

            return GoldDataResponse(data=data)

        except Exception as e:
            logger.error(f"Error getting gold data: {str(e)}")
            return GoldDataResponse(data=[])

    async def _get_latest_records(self) -> GoldDataResponse:
        """Get latest records for realtime data (day=0)"""
        logger.info(f"Getting latest gold records")

        try:
            collection = self._get_collection()

            # Get latest record sorted by datetime
            cursor = collection.find().sort("datetime", -1).limit(1)
            raw_data = list(cursor)

            logger.info(f"Found {len(raw_data)} latest gold records")

            # Convert to model objects
            data = []
            for item in raw_data:
                try:
                    # Convert ObjectId to string if present
                    if "_id" in item:
                        item["_id"] = str(item["_id"])

                    # Convert datetime to string format with minutes
                    if "datetime" in item and isinstance(item["datetime"], datetime):
                        item["datetime"] = item["datetime"].strftime(
                            "%Y-%m-%d %H:%M:%S"
                        )

                    gold_model = GoldDataModel(**item)
                    data.append(gold_model)
                except Exception as e:
                    logger.warning(
                        f"Error parsing latest gold item: {str(e)}, item: {item}"
                    )
                    continue

            return GoldDataResponse(data=data)

        except Exception as e:
            logger.error(f"Error getting latest gold records: {str(e)}")
            return GoldDataResponse(data=[])


# Global service instance
_gold_data_service = None


def get_gold_data_service() -> GoldDataService:
    """Singleton for GoldDataService"""
    global _gold_data_service
    if _gold_data_service is None:
        _gold_data_service = GoldDataService()
    return _gold_data_service
