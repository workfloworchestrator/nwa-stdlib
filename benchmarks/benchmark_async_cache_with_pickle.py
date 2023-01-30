import asyncio
import logging

import structlog
from redis.asyncio import Redis as AIORedis
from shared import REPEAT, get_big_dict, timeit

from nwastdlib.asyncio_cache import cached_result

cache: AIORedis = AIORedis(host="127.0.0.1", port=6379)

logger = structlog.get_logger(__name__)
structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))


@cached_result(cache, "test-suite", None, "pickle", expiry_seconds=2000)
async def pickle_without_checksum_results():
    return await get_big_dict()


@timeit
async def time_pickle_without_checksum_results():
    for _ in range(0, REPEAT):
        await pickle_without_checksum_results()


@cached_result(cache, "test-suite", "SECRETKEY", "secure-pickle", expiry_seconds=2000)
async def pickle_with_checksum_results():
    return await get_big_dict()


@timeit
async def time_pickle_with_checksum_results():
    for _ in range(0, REPEAT):
        await pickle_with_checksum_results()


loop = asyncio.get_event_loop()
# warm the cache:
loop.run_until_complete(pickle_without_checksum_results())
loop.run_until_complete(time_pickle_without_checksum_results())
# warm the cache:
loop.run_until_complete(pickle_with_checksum_results())
loop.run_until_complete(time_pickle_with_checksum_results())
loop.close()
