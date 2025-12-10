from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

class Database:
    """
    Singleton class to handle MongoDB connections.
    Ensures only one connection exists for the entire lifecycle.
    """
    _client = None
    _db = None

    @classmethod
    def connect(cls, uri="mongodb://localhost:27017/", db_name="DentalClinicDB"):
        if cls._client is None:
            try:
                cls._client = MongoClient(uri, serverSelectionTimeoutMS=5000)
                # Verify connection
                cls._client.admin.command('ping')
                cls._db = cls._client[db_name]
                print(f"[OK] [DB] Connected to MongoDB: {db_name}")
            except ConnectionFailure:
                print("[FAIL] [DB] Failed to connect. Is MongoDB running?")
                cls._client = None
        return cls._db

    @classmethod
    def get_db(cls):
        if cls._db is None:
            return cls.connect()
        return cls._db
