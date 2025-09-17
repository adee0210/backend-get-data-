import os
from dotenv import load_dotenv

load_dotenv()
MONGO_CONFIG = {
    "host": os.getenv("MONGO_HOST"),
    "port": os.getenv("MONGO_PORT"),
    "user": os.getenv("MONGO_USERNAME"),
    "pass": os.getenv("MONGO_PASSWORD"),
    "auth": os.getenv("MONGO_AUTH_SOURCE"),
}

DB_FUNDING_RATE = {
    "database_name": "funding_rate_db",
    "collection_realtime_name": "realtime",
    "collection_history_name": "history",
}

DB_BTC_DOMINANCE = {
    "database_name": "btc_dominance",
    "collection_history_name": "historical_data",
    "collection_realtime_name": "realtime_data",
}

# Telegram Bot Configuration
TELEGRAM_CONFIG = {
    "bot_token": os.getenv("TELEGRAM_BOT_TOKEN"),
    "chat_id": os.getenv("TELEGRAM_CHAT_ID"),
    "api_url": "https://api.telegram.org/bot",
}

# Data Monitoring Configuration
MONITORING_CONFIG = {
    "funding_rate_check_interval": int(
        os.getenv("FUNDING_RATE_CHECK_INTERVAL", "3600")
    ),  # seconds (default: 1 hour)
    "expected_symbols": os.getenv("MONITORED_SYMBOLS", "BTCUSDT,ETHUSDT,BNBUSDT").split(
        ","
    ),
    "api_check_url": os.getenv("API_CHECK_URL", "http://localhost:8000"),
    "tolerance_minutes": int(
        os.getenv("TOLERANCE_MINUTES", "30")
    ),  # minutes tolerance for late data
}
