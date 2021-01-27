import fakeredis.aioredis
import pytest

from nwastdlib.middleware import AioRedisCache, AioRedisCacheMiddleware


@pytest.mark.asyncio
async def test_aio_redis_cache_connection_failure(capsys):
    cache = AioRedisCache(host="localhost", port=9999, timeout=1)
    assert cache.started is False
    captured = capsys.readouterr()
    await cache.startup()
    assert cache.started is False
    captured = capsys.readouterr()
    assert "patat" in captured.out


@pytest.mark.asyncio
async def test_aio_redis_cache_connect():
    cache = AioRedisCache(_redis=fakeredis.aioredis.create_redis_pool())
    assert cache.started is False
    await cache.startup()
    assert cache.started is True
    await cache.set("test", b"test_value_1")
    no_namespace = await cache.get("test")
    assert no_namespace == b"test_value_1"
    await cache.set("test", b"test_value_2", namespace="my_namespace")
    with_namespace = await cache.get("test", namespace="my_namespace")
    assert with_namespace == b"test_value_2"
