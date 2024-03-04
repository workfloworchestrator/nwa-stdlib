#  Copyright 2019-2024 SURF.
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
from typing import Any, Callable, Protocol, Union, runtime_checkable

import structlog
from redis.asyncio import Redis as AIORedis

logger = structlog.get_logger(__name__)


@runtime_checkable
class SerializerProtocol(Protocol):
    """Abstract base class to specifies how to build yur own serializer."""

    @staticmethod
    def deserialize(data: Any) -> Any: ...

    @staticmethod
    def serialize(data: Any) -> Any: ...


class DefaultSerializer:
    """Implementation of the default protocol that uses pickle."""

    @staticmethod
    def deserialize(data: Any) -> Any:
        return pickle.loads(data)  # noqa S403

    @staticmethod
    def serialize(data: Union[bytes, bytearray, str]) -> Any:
        return pickle.dumps(data)  # noqa S403


def _deserialize(data: Any, serializer: SerializerProtocol) -> Any:
    try:
        data = serializer.deserialize(data)
    except Exception as e:
        logger.error(
            "Cache deserialization failed, returning None, so cache will be overwritten with a new value", error=e
        )
        return None
    return data


def get_hmac_checksum(secret: str, message: Union[bytes, bytearray, str]) -> str:
    if isinstance(message, str):
        message = message.encode()
    h = hmac.new(secret.encode(), message, hashlib.sha512)
    return h.hexdigest()


async def set_cache_value(
    pool: AIORedis, cache_key: str, value: Any, expiry_seconds: int, serializer: SerializerProtocol
) -> None:
    await pool.setex(cache_key, expiry_seconds, serializer.serialize(value))


async def get_cache_value(pool: AIORedis, cache_key: str, serializer: SerializerProtocol) -> Any:
    serialized_value = await pool.get(cache_key)
    return None if serialized_value is None else _deserialize(serialized_value, serializer)


async def set_signed_cache_value(
    pool: AIORedis, secret: str, cache_key: str, value: Any, expiry_seconds: int, serializer: SerializerProtocol
) -> None:
    pickled_value = serializer.serialize(value)
    checksum = get_hmac_checksum(secret, pickled_value)
    pipeline = pool.pipeline()
    pipeline.setex(cache_key, expiry_seconds, pickled_value).setex(
        f"{cache_key}-checksum", expiry_seconds, checksum.encode()
    )
    result_set_cache_value, result_set_cache_checksum = await pipeline.execute()
    if not result_set_cache_value or not result_set_cache_checksum:
        logger.warning(
            "Cache not set", cache_key=cache_key, value_ok=result_set_cache_value, checksum_ok=result_set_cache_checksum
        )


async def get_signed_cache_value(pool: AIORedis, secret: str, cache_key: str, serializer: SerializerProtocol) -> Any:
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
    return _deserialize(pickled_value, serializer)


def cached_result(
    pool: AIORedis,
    prefix: str,
    secret: Union[str, None],
    key_name: Union[str, None] = None,
    expiry_seconds: int = 120,
    serializer: SerializerProtocol = DefaultSerializer,
) -> Callable:
    """Pass returned result objects from a async function call into redis.

    Returns a decorator function that will cache every result of a function to redis. This only works
    for functions with string, int or UUID arguments and result objects that can be serialized by the
    python pickle library. When you provide a `secret` a second key will be stored, containing a checksum.
    That adds another layer of security to prevent malicious code from being executed when trying yo unpickle
    data that an attacker may have tampered with in Redis.

    When the result can be serialized to JSON, and you're using a fast JSON library, like `orjson` you should
    provide your own serializer. In that case you can also disable the hmac signing by providing `secret=None`.

    Note: Serialization errors will raise an Exception but deserialization will fail silently with only a logged error.


    Example:
        Decorate a suitable function with all the default settings like this:::
            @cached_result(pool, "your_app_name", "SECRET_KEY_FOR_HMAC_CHECKSUM")
            def my_cached_function(uuid_arg, string_arg, int_kwarg=1):
                return do_stuff(uuid_arg, string_arg, kwarg)

        The first call is cached and reused for 120s. If the defaults are inadequate use:::
            @cached_result(pool, "your_app_name", "SECRET_KEY_FOR_HMAC_CHECKSUM", "desired_cache_key_name", 1800)
            def my_other_function...

    Args:
        pool: A async redis cache pool.
        secret: used to generate a checksum too ensure cache tampering is not possible. Set to `None` to disable.
        prefix: Prefix for the cache keys generated.
        key_name: When specified the total redis key_name will be "prefix:key_name".
        expiry_seconds: expiration in seconds. Defaults to two minutes (120s).
        serializer: Provide your own Serializer class or use the default pickle.

    Returns:
        decorator function

    """

    def cache_decorator(func: Callable) -> Callable:
        @wraps(func)
        async def func_wrapper(*args: tuple[Any], **kwargs: dict[str, Any]) -> Any:
            python_major, python_minor = sys.version_info[:2]
            if key_name:
                cache_key = f"{prefix}:{python_major}.{python_minor}:{key_name}"
            else:
                # Auto generate a cache key name based on function_name and a hash of the arguments
                # Note: this makes no attempt to handle non-hashable values like lists and sets or other complex objects
                args_and_kwargs_string = (args, frozenset(kwargs.items()))
                cache_key = f"{prefix}:{python_major}.{python_minor}:{func.__name__}{args_and_kwargs_string}"
                logger.debug("Autogenerated a cache key", cache_key=cache_key)

            logger.debug("Cache called with wrapper func", func_name=func.__name__, cache_key=cache_key)
            if secret:
                if (cached_val := await get_signed_cache_value(pool, secret, cache_key, serializer)) is not None:
                    logger.info("Cache contains secure key, serving from cache", func_name=func.__name__)
                    return cached_val
            else:
                if (cached_val := await get_cache_value(pool, cache_key, serializer)) is not None:
                    logger.info("Cache contains key, serving from cache", func_name=func.__name__)
                    return cached_val

            logger.info("Cache doesn't contain key, calling real function", func_name=func.__name__)
            result = await func(*args, **kwargs)
            if secret:
                await set_signed_cache_value(pool, secret, cache_key, result, expiry_seconds, serializer)
            else:
                await set_cache_value(pool, cache_key, result, expiry_seconds, serializer)
            return result

        return func_wrapper

    return cache_decorator
