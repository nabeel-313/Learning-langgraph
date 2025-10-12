import redis
from config.settings import settings
import json
from src.loggers import Logger

logger = Logger(__name__).get_logger()


class RedisClient:
    def __init__(self):
        self.redis_url = settings.REDIS_URL
        self.client = None
        self._connect()

    def _connect(self):
        try:
            self.client = redis.Redis.from_url(
                self.redis_url,
                decode_responses=True,  # Auto decode to strings
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info("✅ Redis connected successfully")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self.client = None

    def is_connected(self):
        try:
            return self.client and self.client.ping()
        except:
            return False

    def set(self, key: str, value: str, expire: int = None):
        """Set key-value pair with optional expiration (seconds)"""
        if not self.is_connected():
            return False
        try:
            if expire:
                self.client.setex(key, expire, value)
            else:
                self.client.set(key, value)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    def get(self, key: str):
        """Get value by key"""
        if not self.is_connected():
            return None
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    def delete(self, key: str):
        """Delete key"""
        if not self.is_connected():
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    def set_json(self, key: str, value: dict, expire: int = None):
        """Set JSON object"""
        return self.set(key, json.dumps(value), expire)

    def get_json(self, key: str):
        """Get JSON object"""
        data = self.get(key)
        return json.loads(data) if data else None

    def exists(self, key: str):
        """Check if key exists"""
        if not self.is_connected():
            return False
        try:
            return self.client.exists(key) == 1
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False


# Global Redis instance
redis_client = RedisClient()
