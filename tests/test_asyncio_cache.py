from unittest.mock import patch

import pytest

from nwastdlib.asyncio_cache import cached_result


@pytest.fixture
def mock_cache():
    # Mock redis dependency
    with patch("redis.asyncio.Redis") as ctx:
        cache = {}

        async def get(name):
            return cache.get(name)

        async def keys(name):
            return cache.get(name)

        async def set(name, content):
            cache[name] = content

        async def setex(name, ttl, content):
            cache[name] = content

        ctx.return_value.get = get
        ctx.return_value.keys = keys
        ctx.return_value.set = set
        ctx.return_value.setex = setex

        yield cache



#
# async def test_cache_decorator(mock_cache):
#     # given
#
#     @cached_result(mock_cache, cache_prefix, app_settings.SESSION_SECRET, "location_codes", cache_lifetime)
#     async def slow_function():
#         pass
#
#     # when
#
#     files = {"attachment": (attachment, content, "image/png")}
#     result = await testfunction
#
