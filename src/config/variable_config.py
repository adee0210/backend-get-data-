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

DB_CLEAN = {
    "database_name": "funding_rate_db",
    "collection_realtime_name": "realtime",
    "collection_history_name": "history",
}
