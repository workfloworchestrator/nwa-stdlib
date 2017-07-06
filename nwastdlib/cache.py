"""
Module containing Basic logic to use the redis cache
"""
from . import Either, Maybe, identity, format_ex, show_ex

import redis
import connexion
import json


def create_pool(host, port=6379, db=0):

    try:
        r = redis.StrictRedis(host=host, port=port, db=db)
        r.ping()
        return Either.Right(r)
    except Exception as e:
        format_ex(e)
        return Either.Left("Cache not available due to: %s" % e)


def handle_query(pool):
    key = connexion.request.full_path

    def resp_parser(pool):
        return Maybe.of(pool.get(key))\
            .map(json.loads)

    return pool.either(
        identity,
        resp_parser
    )


def handle_setter(pool, payload):
    key = connexion.request.full_path

    def set_val(po, payload):
        try:
            payload = json.dumps(payload)
            if po.set(key, payload):
                return Either.Right(Maybe.Some(True))
            else:
                return Either.Left(Maybe.Nothing())
        except:
            return Either.Left(Maybe.Nothing())
    return pool.flatmap(lambda po: set_val(po, payload))\
        .either(
            identity,
            identity
    )


def flush_all(pool):
    try:
        pool.flushdb()
        return Either.Right("Flush Susccesfull")
    except Exception as e:
        format_ex(e)
        return Either.Left(show_ex(e))


def flush_selected(pool, key):
    try:
        def del_key(keyspec):
            pool.delete(keyspec)

        def check_res(res):
            if len(list(filter(lambda x: x == 0, res))) > 0:
                return Either.Left("Some Deletions not done")
            else:
                return Either.Right("Delete completely succesful")

        return pool.map(lambda p: p.keys(key))\
            .map(lambda keys: [del_key(k) for k in keys])\
            .flatmap(check_res)
    except Exception as e:
        format_ex(e)
        return Either.Left(show_ex(e))
