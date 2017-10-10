"""
Module containing Basic logic to use the redis cache
"""
from . import Either, Maybe
from .ex import format_ex

from collections import namedtuple

import redis
import connexion
import pickle
import sys

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
    key = connexion.request.full_path

    def resp_parser(pool):
        if connexion.request.headers.get('nwa-stdlib-no-cache'):
            return Either.Left(None)
        return Maybe.of(pool.get(key))\
            .maybe(
                Either.Left(None),
                lambda x: Either.Right(pickle.loads(x))
        )

    return resp_parser(pool)


def handle_setter(pool, payload):
    key = connexion.request.full_path

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
