from fastapi import APIRouter
from app.cache import redis_client

router = APIRouter(prefix="/travel", tags=["Travel"])


@router.get("/search")
def search_travel(destination: str):
    cache_key = f"travel:{destination.lower()}"
    cached = redis_client.get(cache_key)
    if cached:
        return {"source": "cache", "data": cached}

    # Simulate an expensive API call
    data = f"Top hotels and activities for {destination}"
    redis_client.setex(cache_key, 600, data)  # cache for 10 minutes
    return {"source": "api", "data": data}
