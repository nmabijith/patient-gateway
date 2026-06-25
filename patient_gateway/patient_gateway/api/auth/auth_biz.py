"""Business logic for authentication."""
from django.conf import settings

from patient_gateway.utilities.redis_client import get_redis_client


def _ttl_seconds(key):
    return int(settings.SIMPLE_JWT[key].total_seconds())


def store_tokens_for_user(user, tokens):
    """Store the issued JWTs in Redis, keyed by user, each expiring with the
    token it holds."""
    client = get_redis_client()
    pipe = client.pipeline()
    pipe.set(f'jwt:access:{user.id}', tokens['access'], ex=_ttl_seconds('ACCESS_TOKEN_LIFETIME'))
    pipe.set(f'jwt:refresh:{user.id}', tokens['refresh'], ex=_ttl_seconds('REFRESH_TOKEN_LIFETIME'))
    pipe.execute()
