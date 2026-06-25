"""Shared Redis client."""
import redis
from django.conf import settings

_client = None


def get_redis_client():
    """Return a process-wide Redis client built from settings.REDIS_URL."""
    global _client
    if _client is None:
        _client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client
