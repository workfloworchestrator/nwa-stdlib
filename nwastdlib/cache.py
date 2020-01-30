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

import pickle  # noqa : S403
from collections import namedtuple
from functools import wraps
from itertools import chain
from typing import Any, Callable, Optional
from uuid import UUID

import redis
import structlog
from flask import current_app, has_app_context, has_request_context, jsonify, make_response, request

from . import Either, Maybe, const, identity
from .ex import format_ex

Error = namedtuple("Error", ["status", "key", "message"])
logger = structlog.get_logger(__name__)


def create_pool(host, port=6379, db=0):

    try:
        r = redis.StrictRedis(host=host, port=port, db=db)
        r.ping()
        return Either.Right(r)
    except Exception as e:
        format_ex(e)
        return Either.Left(Error(500, e, "Cache not available due to: {}".format(e)))


def handle_query(pool):
    key = request.full_path

    def resp_parser(pool):
        if request.headers.get("nwa-stdlib-no-cache"):
            return Either.Left(None)
        return Maybe.of(pool.get(key)).maybe(Either.Left(None), lambda x: Either.Right(pickle.loads(x)))  # noqa: S301

    return resp_parser(pool)


def handle_setter(pool, payload):
    key = request.full_path

    def set_val(po, payload):
        try:
            payload = pickle.dumps(payload)
            if po.set(key, payload, 7200):
                return Either.Right("Payload Set")
            else:
                return Either.Left("Nothing to set")
        except Exception as e:
            return Either.Left("Not able to to set the payload due to: {}".format(e))

    return set_val(pool, payload)


def flush_all(pool):
    try:
        pool.flushdb()
        return Either.Right("Successfully flushed the whole cache")

    except Exception as e:
        format_ex(e)
        return Either.Left(Error(500, e, "Problem while flushing the cache: {}".format(e)))


def flush_selected(pool, key):
    try:

        def del_key(keyspec):
            pool.map(lambda x: x.delete(keyspec))

        def check_res(res):
            if len(list(filter(lambda x: x == 0, res))) > 0:
                return Either.Left(Error(400, "Some Deletions not done", "Some Deletions not done"))
            else:
                return Either.Right("Delete of keys for: %s completely succesful".format(key))  # type: ignore

        return pool.map(lambda p: p.keys(key)).map(lambda keys: [del_key(k) for k in keys]).flatmap(check_res)
    except Exception as e:
        format_ex(e)
        return Either.Left(Error(500, e, "Flush unsuccesfull: {}".format(e)))


def write_object(pool: Any, key: str, obj: Any, exp: int) -> Any:
    """Use redis cache to store a python object."""

    def write(r, key, obj, exp):
        try:
            payload = pickle.dumps(obj)
            if r.set(key, payload, exp):
                return Either.Right("Payload set")
            else:
                return Either.Left("Nothing to set")
        except Exception as e:
            return Either.Left("Not able to set the payload due to: {}".format(e))

    return pool.flatmap(lambda x: write(x, key, obj, exp)).either(const(obj), const(obj))


def read_object(pool: Any, key: str) -> Any:
    """Return python object from redis cache."""

    def read(r, key):
        if has_request_context() and request.headers.get("nwa-stdlib-no-cache"):
            return Either.Left(None)
        return Maybe.of(r.get(key)).maybe(Either.Left(None), lambda x: Either.Right(pickle.loads(x)))  # noqa: S301

    return pool.flatmap(lambda r: read(r, key)).either(const(None), identity)


def cached_result(pool: Any = None, prefix: Optional[str] = None, expiry: int = 120) -> Callable:
    """Pass returned result objects from a function call into redis.

    Returns a decorator function that will cache every result of a function to redis. This only works
    for functions with string, int or UUID arguments and result objects that can be serialized by the
    python pickle library.

    Example:
        Decorate a suitable function with all the default settings like this:::
            @cached_result()
            def my_cached_function(uuid_arg, string_arg, int_kwarg=1):
                return do_stuff(uuid_arg, string_arg, kwarg)

        The first call is cached and reused for 120s. If the defaults are inadequate use:::
            @cached_result(pool=redis_cache, prefix="my_prefix", expiry=600)
            def my_other_function...

    Args:
        pool: A redis cache pool. When omitted the current_app.cache will be used.
        prefix: Prefix for the cache keys generated. Defaults to the name of the decorated function.
        expiry: expiration in seconds. Defaults to two minutes (120s).

    Returns:
        decorator function

    """

    def cache_decorator(func: Callable) -> Callable:
        nonlocal prefix
        if prefix is None:
            prefix = func.__name__

        @wraps(func)
        def func_wrapper(*args, **kwargs):
            nonlocal pool
            if pool is None:
                if has_app_context() and hasattr(current_app, "cache"):
                    pool = current_app.cache
                else:
                    return func(*args, **kwargs)

            components = [prefix]
            for arg in chain(args, kwargs.values()):
                if isinstance(arg, str):
                    components.append(arg)
                if isinstance(arg, int):
                    components.append(str(arg))
                if isinstance(arg, UUID):
                    components.append(str(arg))
            cache_key = ":".join(components)
            result = read_object(pool, cache_key)
            if result:
                return result
            else:
                return write_object(pool, cache_key, func(*args, **kwargs), expiry)

        return func_wrapper

    return cache_decorator


def cached_json_endpoint(pool: Any = None, expiry: int = 3600) -> Callable:
    """Handle cache for flask json_endpoints."""

    def cache_decorator(func: Callable) -> Callable:
        @wraps(func)
        def func_wrapper(*args, **kwargs):
            nonlocal pool, expiry
            if pool is None:
                if has_app_context() and hasattr(current_app, "cache"):
                    pool = current_app.cache
                else:
                    return func(*args, **kwargs)

            if pool.isleft():
                logger.error(pool.value.message)
                body, status = func(*args, **kwargs)
                return make_response(jsonify(body), status)

            cache_key = request.full_path

            if request.headers.get("nwa-stdlib-no-cache"):
                logger.info(
                    "@cached_json_endpoint %s nwa-stdlib-no-cache header detected for %s", func.__name__, cache_key
                )
                result = None
            else:
                result = pool.either(const(None), lambda p: p.get(cache_key))

            if result:
                logger.info("@cached_json_endpoint %s cache hit on %s", func.__name__, cache_key)
                response = make_response(result, 200)
                response.mimetype = "application/json"
                return response
            else:
                logger.info("@cached_json_endpoint %s cache miss on %s", func.__name__, cache_key)
                body, status = func(*args, **kwargs)
                logger.info("@cached_json_endpoint %s status is %s", func.__name__, status)
                result = jsonify(body)
                if status == 200:
                    cache_success = pool.either(const(False), lambda p: p.set(cache_key, result.get_data(), ex=expiry))
                    if cache_success:
                        logger.info("@cached_json_endpoint %s set success: %s", func.__name__, cache_key)
                    else:
                        logger.info("@cached_json_endpoint %s set failed: %s", func.__name__, cache_key)
                return make_response(result, status)

        return func_wrapper

    return cache_decorator
