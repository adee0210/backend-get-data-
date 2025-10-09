import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.config.mongo_config import MongoDBConfig
from src.config.variable_config import DB_ETF_CANDLESTICK
from src.config.logger_config import logger
from src.dto.etf_candlestick_dto import (
    ETFCandlestickRequest,
    ETFCandlestickResponse,
    RealtimeETFCandlestickRequest,
    RealtimeETFCandlestickResponse,
)
from src.model.etf_candlestick import ETFCandlestickModel, RealtimeETFCandlestickModel


class ETFCandlestickService:
    """Service for ETF candlestick data operations"""

    def __init__(self):
        self.mongo_config = MongoDBConfig()
        self.db_config = DB_ETF_CANDLESTICK

    def _get_collection(self):
        """Get MongoDB collection (both historical and latest use same collection)"""
        client = self.mongo_config.get_client()
        db = client[self.db_config["database_name"]]
        collection_name = self.db_config["collection_history_name"]
        return db[collection_name]

    async def _query_by_date_range(self, collection, symbol: str, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Query ETF data using datetime field with YYYY-MM-DD format"""
        
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")
        
        strategies = [
            # Strategy 1: Direct string comparison with symbol filter
            {
                "symbol": symbol,
                "datetime": {
                    "$gte": start_date_str,
                    "$lte": end_date_str
                }
            },
            
            # Strategy 2: Symbol filter only (if date range fails)
            {
                "symbol": symbol
            }
        ]

        for i, strategy in enumerate(strategies, 1):
            try:
                logger.info(f"ETF Strategy {i} for symbol {symbol}: {strategy}")
                cursor = collection.find(strategy).sort("datetime", -1)
                results = list(cursor)
                
                if results:
                    logger.info(f"ETF Strategy {i} found {len(results)} records for {symbol}")
                    return results
                else:
                    logger.warning(f"ETF Strategy {i} returned no results for {symbol}")
                    
            except Exception as e:
                logger.error(f"ETF Strategy {i} failed for {symbol}: {str(e)}")
                continue

        return []

    async def get_etf_candlestick_data(self, request: ETFCandlestickRequest) -> ETFCandlestickResponse:
        """Get historical ETF candlestick data"""
        logger.info(f"Getting ETF candlestick data for {request.day} days, symbol: {request.symbol}")
        
        if request.day == 0:
            # day=0 means realtime (latest records)
            return await self._get_latest_records(request.symbol)
        
        try:
            collection = self._get_collection()
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=request.day)
            
            logger.info(f"ETF Date range for {request.symbol}: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Query data using date range strategy
            raw_data = await self._query_by_date_range(collection, request.symbol, start_date, end_date)
            
            logger.info(f"Found {len(raw_data)} ETF records for {request.symbol}")
            
            # Convert to model objects
            data = []
            for item in raw_data:
                try:
                    # Convert ObjectId to string if present
                    if "_id" in item:
                        item["_id"] = str(item["_id"])
                    
                    etf_model = ETFCandlestickModel(**item)
                    data.append(etf_model)
                except Exception as e:
                    logger.warning(f"Error parsing ETF item: {str(e)}, item: {item}")
                    continue
            
            logger.info(f"Successfully processed {len(data)} ETF records")
            
            return ETFCandlestickResponse(
                data=data
            )
            
        except Exception as e:
            logger.error(f"Error getting ETF candlestick data: {str(e)}")
            return ETFCandlestickResponse(
                data=[]
            )

    async def _get_latest_records(self, symbol: str) -> ETFCandlestickResponse:
        """Get latest records for realtime data (day=0)"""
        logger.info(f"Getting latest ETF candlestick records for symbol: {symbol}")
        
        try:
            collection = self._get_collection()
            
            # Get latest record for specific symbol sorted by datetime
            cursor = collection.find({"symbol": symbol}).sort("datetime", -1).limit(1)
            raw_data = list(cursor)
            
            logger.info(f"Found {len(raw_data)} latest ETF records for {symbol}")
            
            # Convert to model objects
            data = []
            for item in raw_data:
                try:
                    # Convert ObjectId to string if present
                    if "_id" in item:
                        item["_id"] = str(item["_id"])
                    
                    etf_model = ETFCandlestickModel(**item)
                    data.append(etf_model)
                except Exception as e:
                    logger.warning(f"Error parsing latest ETF item: {str(e)}, item: {item}")
                    continue
            
            return ETFCandlestickResponse(
                data=data
            )
            
        except Exception as e:
            logger.error(f"Error getting latest ETF records: {str(e)}")
            return ETFCandlestickResponse(
                data=[]
            )


# Global service instance
_etf_candlestick_service = None


def get_etf_candlestick_service() -> ETFCandlestickService:
    """Singleton for ETFCandlestickService"""
    global _etf_candlestick_service
    if _etf_candlestick_service is None:
        _etf_candlestick_service = ETFCandlestickService()
    return _etf_candlestick_service