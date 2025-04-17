import json
import sys
from copy import copy
from datetime import datetime
from typing import Any, Optional, Union
from uuid import UUID

import pytest
from fakeredis.aioredis import FakeRedis

from nwastdlib.asyncio_cache import _generate_cache_key_suffix, cached_result


@pytest.fixture(autouse=True)
async def clear_fake_redis():
    redis = FakeRedis()
    await redis.flushdb()


class JsonSerializer:
    """A class that implements a simple JSON serializer/deserializer."""

    @staticmethod
    def deserialize(data):
        return json.loads(data)

    @staticmethod
    def serialize(data):
        return json.dumps(data)


async def test_cache_decorator_with_predefined_key():
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


async def test_cache_decorator_without_hmac():
    redis = FakeRedis()
    value = 0

    @cached_result(redis, "test-suite", None, "keyname")
    async def slow_function():
        return value

    result = await slow_function()
    assert result == 0

    # change the value so we can verify that the function was not called
    value = 1

    # A new call should still serve 0: as it is cached now
    result = await slow_function()
    assert result == 0


async def test_cache_decorator_with_json_serializer():
    redis = FakeRedis()
    original_value = {"a": 1, "b": {"c": "string"}, "c": [1, 2, 3]}
    value = copy(original_value)

    @cached_result(redis, "test-suite", None, "keyname", 10, JsonSerializer)
    async def slow_function():
        return value

    result = await slow_function()
    assert result == original_value

    # change the value so we can verify that the function was not called
    value = {"a": 1}
    #
    # # A new call should still serve 0: as it is cached now
    result = await slow_function()
    assert result == original_value


async def test_cache_decorator_with_revalidation_fn():
    redis = FakeRedis()
    value = 0

    def revalidate_fn(*args, **kwargs):
        return kwargs["revalidate_cache"]

    @cached_result(redis, "test-suite", "SECRETNAME", "keyname", revalidate_fn=revalidate_fn)
    async def slow_function(revalidate_cache: bool):
        return value

    result = await slow_function(revalidate_cache=False)
    assert result == 0

    # change the value so we can verify that the function was not called
    value = 1

    # A new call should still serve 0: as it is cached now
    result = await slow_function(revalidate_cache=False)
    assert result == 0


async def test_cache_decorator_with_revalidation_fn_no_cache():
    redis = FakeRedis()
    value = 0

    def revalidate_fn(*args, **kwargs):
        return kwargs["revalidate_cache"]

    @cached_result(redis, "test-suite", "SECRETNAME", "keyname", revalidate_fn=revalidate_fn)
    async def slow_function(revalidate_cache: bool):
        return value

    result = await slow_function(revalidate_cache=True)
    assert result == 0

    # change the value so we can verify that the function was called
    value = 1

    # A new call should serve 1: as it is not cached now
    result = await slow_function(revalidate_cache=True)
    assert result == 1


# Test the validation


@pytest.mark.parametrize(
    "type_",
    [
        Any,
        tuple,
        Union[str, int],
    ],
)
def test_validate_signature_warn_unsafe(type_):
    with pytest.warns(UserWarning, match="unsafe type"):

        @cached_result(FakeRedis(), "test-suite", "SECRETNAME")
        async def foo(param: type_):
            return f"{param}-{param}"


@pytest.mark.parametrize(
    "type_",
    [
        int,
        int | None,
        Optional[int],
    ],
)
def test_validate_signature_safe(recwarn, type_):
    @cached_result(FakeRedis(), "test-suite", "SECRETNAME")
    async def foo(param: type_):
        return f"{param}-{param}"

    assert not [w.message for w in recwarn]


def test_type_error_on_function():
    with pytest.raises(TypeError, match="foo: not a coroutine"):

        @cached_result(FakeRedis(), "test-suite", "SECRETNAME")
        def foo(param: str):
            return f"{param}-{param}"


def test_type_error_on_generatorfunction():
    with pytest.raises(TypeError, match="foo: not a coroutine"):

        @cached_result(FakeRedis(), "test-suite", "SECRETNAME")
        def foo(param: str):
            yield f"{param}-{param}"


def test_type_error_on_asyncgeneratorfunction():
    with pytest.raises(TypeError, match="foo: not a coroutine"):

        @cached_result(FakeRedis(), "test-suite", "SECRETNAME")
        async def foo(param: str):
            yield f"{param}-{param}"


# Test key generation

version = f"{sys.version_info.major}.{sys.version_info.minor}"
cache_prefix = "test"
cache_key_start = f"{cache_prefix}:{version}"


@pytest.mark.parametrize(
    ("skip_first", "args", "kwargs", "expected_key"),
    [
        (True, (1, 2), {}, "((2,), frozenset())"),
        (False, (1, 2), {}, "((1, 2), frozenset())"),
        (False, (1, "a"), {}, "((1, 'a'), frozenset())"),
        (False, (), {"foo": "bar"}, "((), frozenset({('foo', 'bar')}))"),
        (False, (1.234567,), {}, "((1.234567,), frozenset())"),
        (False, (datetime(year=2025, month=4, day=14),), {}, "((datetime.datetime(2025, 4, 14, 0, 0),), frozenset())"),
        (
            False,
            (UUID("12345678-0000-1111-2222-0123456789ab"),),
            {},
            "((UUID('12345678-0000-1111-2222-0123456789ab'),), frozenset())",
        ),
        (False, (), {}, None),
    ],
)
def test_generate_cache_key_suffix(skip_first, args, kwargs, expected_key):
    assert _generate_cache_key_suffix(skip_first=skip_first, args=args, kwargs=kwargs) == expected_key
