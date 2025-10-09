from typing import List, Optional
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

    def _parse_date_string(self, date_str: str) -> datetime:
        """Parse date string from DDMMYYYY format to datetime object"""
        try:
            # Parse DDMMYYYY format
            day = int(date_str[:2])
            month = int(date_str[2:4])
            year = int(date_str[4:8])
            return datetime(year, month, day)
        except Exception as e:
            logger.error(f"Error parsing date string {date_str}: {str(e)}")
            raise ValueError(
                f"Invalid date format: {date_str}. Expected DDMMYYYY format."
            )

    async def get_gold_data(self, request: GoldDataRequest) -> GoldDataResponse:
        """Get historical gold data"""
        logger.info(
            f"Getting gold data - day: {request.day}, from_date: {request.from_date}, to_date: {request.to_date}"
        )

        # Handle different parameter combinations
        if request.from_date and request.to_date:
            return await self._get_data_by_date_range(
                request.from_date, request.to_date, request.day
            )

        # Handle day parameter
        day = request.day if request.day is not None else 1

        if day == 0:
            # day=0 means realtime (latest records)
            return await self._get_latest_records()

        try:
            collection = self._get_collection()

            # Calculate date range (day-based)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=day)

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

    async def _get_data_by_date_range(
        self, from_date: str, to_date: str, day: Optional[int] = None
    ) -> GoldDataResponse:
        """Get gold data by date range"""
        try:
            # Parse dates from DDMMYYYY format
            from_dt = self._parse_date_string(from_date)
            to_dt = self._parse_date_string(to_date)

            # Nếu có day, tính toán lại from_date dựa trên to_date
            if day is not None:
                calculated_from = to_dt - timedelta(days=day)
                # Sử dụng ngày muộn hơn giữa from_dt và calculated_from
                from_dt = max(from_dt, calculated_from)

            # Set thời gian bắt đầu và kết thúc cho ngày
            start_date = from_dt.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = to_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

            logger.info(f"Gold date range query: {start_date} to {end_date}")

            collection = self._get_collection()

            # Query by date range using existing method
            raw_data = await self._query_by_date_range(collection, start_date, end_date)

            logger.info(f"Found {len(raw_data)} gold records in date range")

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
                    logger.warning(f"Error parsing gold item in date range: {str(e)}")
                    continue

            return GoldDataResponse(data=data)

        except Exception as e:
            logger.error(f"Error in gold date range query: {str(e)}")
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
