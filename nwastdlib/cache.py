"""
Module containing Basic logic to use the redis cache
"""
import pickle
import sys
from collections import namedtuple
from functools import wraps
from itertools import chain
from uuid import UUID

import redis
from flask import request, has_app_context, current_app

from . import Either, Maybe, const, identity
from .ex import format_ex
from typing import Callable, Any, Optional

Error = namedtuple("Error", ["status", "key", "message"])


def create_pool(host, port=6379, db=0):

    try:
        r = redis.StrictRedis(host=host, port=port, db=db)
        r.ping()
        return Either.Right(r)
    except Exception as e:
        format_ex(e)
        return Either.Left(Error(500, e, "Cache not available due to: %s" % e))


def handle_query(pool):
    key = request.full_path

    def resp_parser(pool):
        if request.headers.get('nwa-stdlib-no-cache'):
            return Either.Left(None)
        return Maybe.of(pool.get(key))\
            .maybe(
                Either.Left(None),
                lambda x: Either.Right(pickle.loads(x))
        )

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
            print("Not able to to set the payload due to: %s" % e, file=sys.stderr)
            return Either.Left("Not able to to set the payload due to: %s" % e)
    return set_val(pool, payload)


def flush_all(pool):
    try:
        pool.flushdb()
        return Either.Right("Successfully flushed the whole cache")

    except Exception as e:
        format_ex(e)
        return Either.Left(Error(500, e, "Problem while flushing the cache: %s" % e))


def flush_selected(pool, key):
    try:
        def del_key(keyspec):
            pool.map(lambda x: x.delete(keyspec))

        def check_res(res):
            if len(list(filter(lambda x: x == 0, res))) > 0:
                return Either.Left(Error(400, "Some Deletions not done", "Some Deletions not done"))
            else:
                return Either.Right("Delete of keys for: %s completely succesful" % key)

        return pool.map(lambda p: p.keys(key))\
            .map(lambda keys: [del_key(k) for k in keys])\
            .flatmap(check_res)
    except Exception as e:
        format_ex(e)
        return Either.Left(Error(500, e, "Flush unsuccesfull: %s" % e))


def write_object(pool: Any, key: str, obj: Any, exp: int) -> Any:
    """Use redis cache to store a python object"""

    def write(r, key, obj, exp):
        try:
            payload = pickle.dumps(obj)
            if r.set(key, payload, exp):
                return Either.Right("Payload set")
            else:
                return Either.Left("Nothing to set")
        except Exception as e:
            return Either.Left("Not able to set the payload due to: %s" % e)

    return pool.flatmap(lambda x: write(x, key, obj, exp)) \
        .either(const(obj), const(obj))


def read_object(pool: Any, key: str) -> Any:
    """Return python object from redis cache"""

    def read(r, key):
        if request.headers.get('nwa-stdlib-no-cache'):
            return Either.Left(None)
        return Maybe.of(r.get(key))\
            .maybe(
                Either.Left(None),
                lambda x: Either.Right(pickle.loads(x))
        )

    return pool.flatmap(lambda r: read(r, key)).either(const(None), identity)


def cached_result(pool: Any=None, prefix: Optional[str]=None, expiry: int=120) -> Callable:
    """Decorator to cache returned result objects from a function call into redis

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
                if has_app_context() and hasattr(current_app, 'cache'):
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
