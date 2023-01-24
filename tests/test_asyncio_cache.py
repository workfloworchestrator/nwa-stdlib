import sys

from fakeredis.aioredis import FakeRedis

from nwastdlib.asyncio_cache import cached_result


async def test_cache_decorator_with_predefined_key(caplog):
    redis = FakeRedis()
    value = 0

    @cached_result(redis, "test-suite", "SECRETNAME", "keyname")
    async def slow_function():
        return value

    result = await slow_function()
    assert result == 0

    # change the value so we can verify that the function was not called
    value = 1

    # A new call should still serve 0: as it is cached now
    result = await slow_function()
    assert result == 0


async def test_cache_decorator_with_auto_generated_key():
    redis = FakeRedis()
    value = 0

    @cached_result(redis, "test-suite", "SECRETNAME")
    async def slow_function(a, b=11):
        return value

    result = await slow_function(3, 11)
    assert result == 0

    # change the value so we can verify that the function was not called
    value = 1

    # A new call should still serve 0: as it is cached now
    result = await slow_function(3, 11)
    assert result == 0

    # A call to function with other parameters should serve the new value:
    result = await slow_function(3, 12)
    assert result == 1


async def test_cache_decorator_with_auto_generated_key_and_kwargs():
    redis = FakeRedis()
    value = 0

    @cached_result(redis, "test-suite", "SECRETNAME")
    async def slow_function(a, b=11, **kwargs):
        return value

    result = await slow_function(3, 11, c=15)
    assert result == 0

    # change the value so we can verify that the function was not called
    value = 1

    # A new call should still serve 0: as it is cached now
    result = await slow_function(3, 11, c=15)
    assert result == 0

    # A call to function with other parameters should serve the new value:
    result = await slow_function(3, 11, c=16)
    assert result == 1


async def test_cache_decorator_wrong_checksum():
    redis = FakeRedis()
    python_major, python_minor = sys.version_info[:2]

    value = 0

    @cached_result(redis, "test-suite", "SECRETNAME", "keyname")
    async def slow_function():
        return value

    result = await slow_function()
    assert result == 0

    # change the value, so we can verify that the function was re-called
    value = 1

    # patch the checksum value
    await redis.setex(f"test-suite:{python_major}.{python_minor}:keyname-checksum", 120, "123456789")

    # A new call should return 1: due to the checksum error the function is called again
    result = await slow_function()
    assert result == 1


async def test_cache_decorator_wrong_data():
    redis = FakeRedis()
    python_major, python_minor = sys.version_info[:2]

    value = 0

    @cached_result(redis, "test-suite", "SECRETNAME", "keyname")
    async def slow_function():
        return value

    result = await slow_function()
    assert result == 0

    # change the value, so we can verify that the function was re-called
    value = 1

    # patch the cache value
    await redis.setex(f"test-suite:{python_major}.{python_minor}:keyname", 120, b"faked_data")

    # A new call should return 1: due to the checksum error the function is called again
    result = await slow_function()
    assert result == 1
