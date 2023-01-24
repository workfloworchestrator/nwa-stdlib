#  Copyright 2019 SURF.
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#          http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
import hashlib
import hmac
import pickle  # noqa S403
import sys
from functools import wraps
from typing import Any, Callable

import structlog
from redis.asyncio import Redis as AIORedis

logger = structlog.get_logger(__name__)


def deserialize(data: Any) -> Any:
    return pickle.loads(data)  # noqa S403


def serialize(data: Any) -> Any:
    return pickle.dumps(data)  # noqa S403


def get_hmac_checksum(secret: str, message: bytearray) -> str:
    h = hmac.new(secret.encode(), message, hashlib.sha512)
    return h.hexdigest()


async def set_signed_cache_value(pool: AIORedis, secret: str, cache_key: str, value: Any, expiry_seconds: int) -> None:
    pickled_value = serialize(value)
    checksum = get_hmac_checksum(secret, pickled_value)
    pipeline = pool.pipeline()
    pipeline.setex(cache_key, expiry_seconds, pickle.dumps(value)).setex(
        f"{cache_key}-checksum", expiry_seconds, checksum.encode()
    )
    result1, result2 = await pipeline.execute()
    if not result1 or not result2:
        logger.warning("Cache not set", cache_key=cache_key, value_ok=result1, checksum_ok=result2)


async def get_signed_cache_value(pool: AIORedis, secret: str, cache_key: str) -> Any:
    pipeline = pool.pipeline()
    pipeline.get(cache_key).get(f"{cache_key}-checksum")
    pickled_value, cache_checksum = await pipeline.execute()
    if not pickled_value or not cache_checksum:
        return None

    cache_checksum = cache_checksum.decode("utf-8")
    if (checksum := get_hmac_checksum(secret, pickled_value)) != cache_checksum:
        logger.error(
            "Checksum for cache was wrong, someone tampered with the values!",
            correct_checksum=str(cache_checksum),
            recalculated_checksum=checksum,
        )
        return None

    try:
        data = deserialize(pickled_value)
    except Exception as e:
        logger.error(
            "Cache deserialization failed, returning None, so cache will be overwritten with a new value", error=e
        )
        return None
    return data


def cached_result(
    pool: AIORedis, prefix: str, secret: str, key_name: str | None = None, expiry_seconds: int = 120
) -> Callable:
    """Pass returned result objects from a function call into redis.

    Returns a decorator function that will cache every result of a function to redis. This only works
    for functions with string, int or UUID arguments and result objects that can be serialized by the
    python pickle library.

    Example:
        Decorate a suitable function with all the default settings like this:::
            @cached_result(pool, "your_app_name", "SECRET_KEY_FOR_HMAC_CHECKSUM")
            def my_cached_function(uuid_arg, string_arg, int_kwarg=1):
                return do_stuff(uuid_arg, string_arg, kwarg)

        The first call is cached and reused for 120s. If the defaults are inadequate use:::
            @cached_result(pool, "your_app_name", "SECRET_KEY_FOR_HMAC_CHECKSUM", "desired_cache_key_name", 120)
            def my_other_function...

    Args:
        pool: A async redis cache pool.
        secret: used to generate a checksum too ensure cache tampering is not possible.
        prefix: Prefix for the cache keys generated.
        key_name: When specified the total redis key_name will be "prefix:key_name".
        expiry_seconds: expiration in seconds. Defaults to two minutes (120s).

    Returns:
        decorator function

    """

    def cache_decorator(func: Callable) -> Callable:
        @wraps(func)
        async def func_wrapper(*args: tuple[Any], **kwargs: dict[str, Any]) -> Callable:
            python_major, python_minor = sys.version_info[:2]
            if key_name:
                cache_key = f"{prefix}:{python_major}.{python_minor}:{key_name}"
            else:
                # Auto generate a cache key name based on function_name and a hash of the arguments
                # Note: this makes no attempt to handle non-hashable values like lists and sets or other complex objects
                args_and_kwargs_string = (args, frozenset(kwargs.items()))
                cache_key = f"{prefix}:{python_major}.{python_minor}:{func.__name__}{args_and_kwargs_string}"
                logger.info("CACHE KEY", cache_key=cache_key)

            logger.debug("Cache called with wrapper func", func_name=func.__name__, cache_key=cache_key)
            if (cached_val := await get_signed_cache_value(pool, secret, cache_key)) is not None:
                logger.info("Cache contains key, serving from cache", cache_key=cache_key)
                return cached_val

            logger.info("Cache doesn't contain key, calling real function", cache_key=cache_key)
            result = await func(*args, **kwargs)
            await set_signed_cache_value(pool, secret, cache_key, result, expiry_seconds)
            return result

        return func_wrapper

    return cache_decorator
