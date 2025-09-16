from pymongo import MongoClient
from src.config.variable_config import MONGO_CONFIG, DB_CLEAN


class MongoDBConfig:
    """Singleton wrapper around a pymongo MongoClient using values from
    `src.config.variable_config`.

    Note: `variable_config` uses keys `host`, `port`, `user`, `pass`, `auth`.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConfig, cls).__new__(cls)
            cls._instance.init_config()
            cls._instance._client = None
        return cls._instance

    def init_config(self):
        # normalize keys from variable_config
        self._config = {
            "host": MONGO_CONFIG.get("host") or "localhost",
            "port": int(MONGO_CONFIG.get("port") or 27017),
            "username": MONGO_CONFIG.get("user"),
            "password": MONGO_CONFIG.get("pass"),
            "authSource": MONGO_CONFIG.get("auth"),
        }

    @property
    def config(self):
        return self._config

    def get_client(self):
        if self._client is None:
            # if username/password are not set, rely on unauthenticated connection
            kwargs = {}
            if self._config.get("username"):
                kwargs.update(
                    username=self._config.get("username"),
                    password=self._config.get("password"),
                    authSource=self._config.get("authSource"),
                )

            self._client = MongoClient(
                host=self._config["host"],
                port=self._config["port"],
                **kwargs,
            )
        return self._client


def get_db_and_collections():
    """Return the database name and collection names defined in `DB_CLEAN`.

    This helper mirrors the variable_config structure so other modules can
    import database/collection names from a single place.
    """
    return (
        DB_CLEAN.get("database_name"),
        DB_CLEAN.get("collection_realtime_name"),
        DB_CLEAN.get("collection_history_name"),
    )
