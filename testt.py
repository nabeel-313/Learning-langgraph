from src.cache.redis_client import redis_client
from src.cache.session_manager import session_manager

# Test Redis connection on startup
if redis_client.is_connected():
    print("✅ Redis is connected")
else:
    print("❌ Redis connection failed")
