import functools
import hashlib
import json
import os
import redis
from typing import Any, Optional, Callable


class RedisCache:
    def __init__(self):
        self.redis_url = os.environ.get("REDIS_URL")

        self.client = (
            redis.from_url(
                self.redis_url, decode_responses=True, socket_connect_timeout=10
            )
            if self.redis_url
            else None
        )

        self.default_ttl = 3600

    def _generate_key(self, func_name: str, args: tuple, kwargs: dict) -> str:
        raw_key = f"{func_name}:{str(args)}:{str(sorted(kwargs.items()))}"
        return f"lyrics_cache:{hashlib.md5(raw_key.encode()).hexdigest()}"

    def get(self, key: str) -> Any:
        if not self.client:
            return None
        try:
            data = self.client.get(key)
            return json.loads(data) if data else None
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        if not self.client:
            return
        try:
            ttl = ttl if ttl is not None else self.default_ttl
            self.client.setex(key, ttl, json.dumps(value))
        except Exception:
            pass

    def cached(self, ttl: Optional[int] = None):
        def decorator(func: Callable):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                if not self.client:
                    return func(*args, **kwargs)

                key_args = args[1:] if args and hasattr(args[0], "__dict__") else args
                key = self._generate_key(func.__name__, key_args, kwargs)

                cached_val = self.get(key)
                if cached_val is not None:
                    return cached_val

                result = func(*args, **kwargs)
                if result is not None:
                    self.set(key, result, ttl=ttl)
                return result

            return wrapper

        return decorator


global_cache = RedisCache()
