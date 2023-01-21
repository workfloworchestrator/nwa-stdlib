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
import pickle
from functools import wraps
from typing import Any, Callable

import structlog
from redis.asyncio import Redis as AIORedis

logger = structlog.get_logger(__name__)


def get_hmac_checksum(secret, message):
    # Todo: check if the current secret is good enough for sha512, it might be better to use a new SECRET just for this
    h = hmac.new(secret.encode(), message, hashlib.sha512)
    return h.hexdigest()


async def set_signed_cache_value(pool: AIORedis, secret: str, cache_key: str, value: Any, expiry: int):
    pickled_value = pickle.dumps(value)
    checksum = get_hmac_checksum(secret, pickled_value)
    pipeline = pool.pipeline()
    pipeline.setex(cache_key, expiry, pickle.dumps(value)).setex(f"{cache_key}-checksum", expiry, checksum.encode())
    result1, result2 = await pipeline.execute()
    if not result1 or not result2:
        logger.warning("Cache not set", cache_key=cache_key, value_ok=result1, checksum_ok=result2)


async def get_signed_cache_value(pool: AIORedis, secret: str, cache_key: str):
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

    return pickle.loads(pickled_value)


def cached_result(pool: AIORedis, prefix: str, secret: str, key_name: str | None, expiry: int = 120) -> Callable:
    """Pass returned result objects from a function call into redis.

    Returns a decorator function that will cache every result of a function to redis. This only works
    for functions with string, int or UUID arguments and result objects that can be serialized by the
    python pickle library.

    Example:
        Todo: switch to cPickle?
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
        expiry: expiration in seconds. Defaults to two minutes (120s).

    Returns:
        decorator function

    """

    def cache_decorator(func: Callable) -> Callable:

        # Todo: write a sync implementation?

        @wraps(func)
        async def func_wrapper(*args, **kwargs):
            if key_name:
                cache_key = f"{prefix}:{key_name}"
            else:
                # Auto generate a cache key name based on function_name and a hash of the arguments
                # Note: this makes no attempt to handle non-hashable values like lists and sets or other complex objects
                # Todo: log/warning about key problems for unsupported kwargs argument types?
                kwd_mark = object()  # sentinel for separating args from kwargs
                cache_key = f"{prefix}:" + args + (kwd_mark,) + tuple(sorted(kwargs.items()))

            logger.debug(f"Cache called with wrapper func: {func.__name__}", cache_key=cache_key)
            if (cached_val := await get_signed_cache_value(pool, secret, cache_key)) is not None:
                logger.info("Cache contains key, serving from cache", cache_key=cache_key)
                return cached_val

            logger.info("Cache doesn't contain key, calling real function", cache_key=cache_key)
            result = await func(*args, **kwargs)
            await set_signed_cache_value(pool, secret, cache_key, result, expiry)
            return result

        return func_wrapper

    return cache_decorator


# def cached_json_endpoint(pool: Any = None, expiry: int = 3600) -> Callable:
#     """Handle cache for flask json_endpoints."""
#
#     def cache_decorator(func: Callable) -> Callable:
#         @wraps(func)
#         def func_wrapper(*args, **kwargs):
#             nonlocal pool, expiry
#             if pool is None:
#                 if has_app_context() and hasattr(current_app, "cache"):
#                     pool = current_app.cache
#                 else:
#                     return func(*args, **kwargs)
#
#             if pool.isleft():
#                 logger.error(pool.value.message)
#                 body, status = func(*args, **kwargs)
#                 return make_response(jsonify(body), status)
#
#             cache_key = request.full_path
#
#             if request.headers.get("nwa-stdlib-no-cache"):
#                 logger.info(
#                     "@cached_json_endpoint %s nwa-stdlib-no-cache header detected for %s", func.__name__, cache_key
#                 )
#                 result = None
#             else:
#                 result = pool.either(const(None), lambda p: p.get(cache_key))
#
#             if result:
#                 logger.info("@cached_json_endpoint %s cache hit on %s", func.__name__, cache_key)
#                 response = make_response(result, 200)
#                 response.mimetype = "application/json"
#                 return response
#             else:
#                 logger.info("@cached_json_endpoint %s cache miss on %s", func.__name__, cache_key)
#                 body, status = func(*args, **kwargs)
#                 logger.info("@cached_json_endpoint %s status is %s", func.__name__, status)
#                 result = jsonify(body)
#                 if status == 200:
#                     cache_success = pool.either(const(False), lambda p: p.set(cache_key, result.get_data(), ex=expiry))
#                     if cache_success:
#                         logger.info("@cached_json_endpoint %s set success: %s", func.__name__, cache_key)
#                     else:
#                         logger.info("@cached_json_endpoint %s set failed: %s", func.__name__, cache_key)
#                 return make_response(result, status)
#
#         return func_wrapper
#
#     return cache_decorator
