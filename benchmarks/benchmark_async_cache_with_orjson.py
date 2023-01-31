import asyncio

try:
    import orjson
except Exception as e:
    print(f"You'll need orjson to execute this. Error: {e}")  # noqa: T201
import logging

import structlog
from redis.asyncio import Redis as AIORedis
from shared import REPEAT, get_big_dict, timeit

from nwastdlib.asyncio_cache import cached_result

cache: AIORedis = AIORedis(host="127.0.0.1", port=6379)

logger = structlog.get_logger(__name__)
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))


class OrjsonSerializer:
    """A class that implements a simple JSON serializer/deserializer."""

    @staticmethod
    def deserialize(data):
        return orjson.loads(data)

    @staticmethod
    def serialize(data):
        return orjson.dumps(data)


@cached_result(cache, "test-suite", None, "orjson", expiry_seconds=2000, serializer=OrjsonSerializer)
async def orjson_without_checksum_results():
    return await get_big_dict()


@timeit
async def time_orjson_without_checksum_results():
    for _ in range(0, REPEAT):
        await orjson_without_checksum_results()


@cached_result(cache, "test-suite", "SECRETKEY", "secure-orjson", expiry_seconds=2000, serializer=OrjsonSerializer)
async def orjson_with_checksum_results():
    return await get_big_dict()


@timeit
async def time_orjson_with_checksum_results():
    for _ in range(0, REPEAT):
        await orjson_with_checksum_results()


loop = asyncio.get_event_loop()
# warm the cache:
loop.run_until_complete(orjson_without_checksum_results())
loop.run_until_complete(time_orjson_without_checksum_results())
# warm the cache:
loop.run_until_complete(orjson_with_checksum_results())
loop.run_until_complete(time_orjson_with_checksum_results())
loop.close()
