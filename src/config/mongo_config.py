from pymongo import MongoClient
from src.config.variable_config import DB_BTC_DOMINANCE, DB_FUNDING_RATE, MONGO_CONFIG


class MongoDBConfig:
    """Singleton wrapper xung quanh pymongo MongoClient sử dụng giá trị từ
    `src.config.variable_config`.

    Lưu ý: `variable_config` sử dụng các key `host`, `port`, `user`, `pass`, `auth`.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBConfig, cls).__new__(cls)
            cls._instance.init_config()
            cls._instance._client = None
        return cls._instance

    def init_config(self):
        # chuẩn hóa keys từ variable_config
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
            # nếu username/password không được set, sử dụng kết nối không xác thực
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


def get_db_and_collections_funding_rate():
    return (
        DB_FUNDING_RATE.get("database_name"),
        DB_FUNDING_RATE.get("collection_realtime_name"),
        DB_FUNDING_RATE.get("collection_history_name"),
    )

def get_db_and_collections_btcdominance():
    return (
        DB_BTC_DOMINANCE.get("database_name"),
        DB_BTC_DOMINANCE.get("collection_realtime_name"),
        DB_BTC_DOMINANCE.get("collection_history_name"),
    )
