import asyncio
from typing import Optional, Sequence, Tuple

import aioredis
import structlog
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send

AIO_REDIS_CACHE_SCOPE_KEY = "aio_redis_cache"
AIO_REDIS_CACHE_HEADER = "x-aio-redis-cache"
logger = structlog.get_logger(__name__)


class SnoopASGIMiddleware:
    """ASGI Middleware to log the request scope and messages passed over the 'receive' and 'send' awaitables. Useful for debugging ASGI middleware."""

    def __init__(self, app: ASGIApp):
        self.app = app

    def receive(self, original):
        async def proxy():
            message: Message = await original()
            logger.info("ASGI message received.", message=message)
            return message

        return proxy

    def send(self, original):
        async def proxy(message: Message):
            logger.info("ASGI message sent.", message=message)
            return await original(message)

        return proxy

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        safe_scope = {}
        for key, val in scope.items():
            try:
                safe_val = str(val)
                safe_scope[key] = safe_val
            except ValueError:
                safe_scope[key] = repr(val)
        logger.info("scope", **safe_scope)
        return await self.app(scope, self.receive(receive), self.send(send))


class AioRedisCache:
    """Wrapper class to initialize and use an aioredis connection pool as cache."""

    def __init__(
        self,
        host="127.0.0.1",
        port=6793,
        db=0,
        encoding="utf-8",
        timeout=15,
        namespace="aio_redis_cache",
        ttl=1800,
        _redis=None,
    ):
        self.address = f"redis://{host}:{port}/{db}?encoding={encoding}"
        self.timeout = timeout
        self.namespace = namespace
        self.default_ttl = ttl
        self.timeout = timeout
        self._redis = _redis
        self.pool = None
        self.started = False

    async def startup(self):
        if self._redis:
            # This was added to be able to unit test with fakeredis or birdisle
            self.pool = await self._redis
            self.started = True
            return
        logger.info("Starting up redis pool")
        try:
            self.pool = await aioredis.create_redis_pool(self.address, timeout=self.timeout)
            self.started = True
        except (asyncio.TimeoutError, aioredis.RedisError, OSError):
            logger.error(
                "Failed to connect to configured Redis instance. Cache is unavailable",
                address=self.address,
                exc_info=True,
            )

    async def shutdown(self):
        if self.pool:
            logger.info("Shutting down redis pool")
            self.pool.close()
            await self.pool.wait_closed()

    def key_builder(self, name: str, namespace: Optional[str]) -> str:
        parts = []
        if self.namespace:
            parts.append(self.namespace)
        if namespace:
            parts.append(namespace)
        parts.append(name)
        return ":".join(parts)

    async def get(self, name: str, namespace: Optional[str] = None) -> Optional[bytes]:
        if not self.started:
            logger.info("redis cache has not been initialized.")
            return None
        key = self.key_builder(name, namespace)
        try:
            return await self.pool.get(key)
        except aioredis.RedisError:
            logger.error("Fetching data from redis failed.", key=key, exc_info=True)
            return None

    async def set(self, name: str, value: bytes, namespace=None, ttl=None):
        if not self.started:
            logger.info("redis cache has not been initialized")
            return None
        key = self.key_builder(name, namespace)
        logger.info("set called", key=key)
        try:
            await self.pool.set(key, value, expire=ttl or self.default_ttl)
        except aioredis.RedisError:
            logger.error("Putting data into redis failed.", key=key, exc_info=True)


class AioRedisCacheMiddleware:
    """"Middleware used to inject a AioRedisCache and CachingProy instance into the ASGI asynchronous call chain."""

    def __init__(self, app: ASGIApp, cache: AioRedisCache):
        self.app = app
        self.cache = cache

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http" or self.cache is None or not self.cache.started:
            await self.app(scope, receive, send)
            return

        # Adding a reference to the scope makes it accessible during the whole request
        # This is simpler than using a ContextVar or a singleton class for the cache
        scope[AIO_REDIS_CACHE_SCOPE_KEY] = self.cache

        if scope["method"] == "GET":

            scope["app"].state.aio_redis_cache = self.cache
            caching_proxy = CachingProxy(self.app, self.cache)
            await caching_proxy(scope, receive, send)
        else:
            await self.app(scope, receive, send)


class CachingProxy:
    """ASGI app to cache outgoing http body in to an AioRedisCache."""

    def __init__(self, app: ASGIApp, cache: AioRedisCache):
        self.app = app
        self.cache = cache
        self.do_store = False
        self.namespace = None
        self.ttl = None
        self.chunks = []
        self.original_send = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        """Proxy message pushed to the send queue to be able to cache the http body."""
        self.original_send = send
        self.path = scope["path"]
        await self.app(scope, receive, self._send)

    async def _send(self, message: Message):
        """Cache the response body when the headers include our cache instructions."""
        if message["type"] == "http.response.start" and message["status"] == 200:
            self.parse_headers(message["headers"])
        elif message["type"] == "http.response.body" and self.do_store:
            self.chunks.append(message["body"])
            if not message["more_body"]:
                body = b"".join(self.chunks)
                logger.info("caching....")
                await self.cache.set(self.path, body, namespace=self.namespace, ttl=self.ttl)
        # note: Switching the order of awaiting cache and original send did not work. The last call to send doesn't seem to ever return back control.
        await self.original_send(message)

    def parse_headers(self, headers: Sequence[Tuple[bytes, bytes]]):
        """Parse our cache instructions from the headers.

        The header name is set in the AIO_REDIS_CACHE_HEADER module level constant and is currently `x-aio-redis-cache`.
        Example headers:
            To instruct the middleware to not store data.
              *x-aio-redis-cache: no-store*
            To instruct to add an extra namespae.
              *x-aio-redis-cache: namespace=surf:net*
            To instruct to use a ttl of 300 seconds.
              *x-aio-redis-cache: ttl=300*
            Combine namespace and ttl instruction.
              *x-aio-redis-cache: namespace=surf:net; ttl=300*
        """
        for name, value in headers:
            if name.decode() == AIO_REDIS_CACHE_HEADER:
                for part in value.split(b"; "):
                    keyval = part.split(b"=")
                    if keyval[0] == b"defaults":
                        self.do_store = True
                    elif keyval[0] == b"no-store":
                        self.do_store = False
                    elif keyval[0] == b"namespace":
                        self.namespace = keyval[1].decode()
                        self.do_store = True
                    elif keyval[0] == b"ttl":
                        self.ttl = int(keyval[1])
                        self.do_store = True
                    else:
                        logger.error("Unrecognized header statement", header=value)


class CachedDataDependency:
    """Use this class in the FastAPI dependency injection system to get a cached piece of data from the cache.


    Example:
        from FastAPI import Depends, Response

        async def my_endpoint(cached_data = Depends(CachedDataDependency(namespace="example:com", ttl=300)):
            if cached_data:
                return Response(cached_data, media_type="application/json")
            return await my_long_running_call()

    """

    def __init__(self, namespace=None, ttl=None):
        self.namespace = namespace
        self.ttl = ttl

    def create_header(self, cached_data: Optional[bytes]):
        """Create a header to instruct the middleware.

        See CachingProxy.parse_headers for examples of valid headers.
        """
        if cached_data:
            return "no-store"
        if self.namespace and self.ttl:
            return f"namespace={self.namespace}; ttl={self.ttl}"
        if self.namespace:
            return f"namespace={self.namespace}"
        if self.ttl:
            return f"ttl={self.ttl}"
        return "defaults"

    async def __call__(self, request: Request, response: Response) -> Optional[bytes]:
        """When this is used as Dependency in the FastAPI dependency injection system the request and response objects will be magically available to manipulate.

        This takes use of non-obvious but documented FastAPI behaviour.
         1) The dependency injection system will instanciate a Request and Response object when they are declared in a dependency.
         2) When a Response object is injected but not returned by an endpoint its headers are merged with the actual Response.
         3) When a Response object is directly returned from an endpoint, no Pydantic validation is performed and no transformation is performed.
         4) All middleware works with the ASGI stream, not the Request/Response objects from FastAPI/Starlette. The BaseHTTPMiddleware class from Starlette converts this back and forth.

        """
        # In starlette every Request object includes the Scope dict.
        cache: Optional[AioRedisCache] = request.get(AIO_REDIS_CACHE_SCOPE_KEY)
        if cache:
            cached_data = await cache.get(request.url.path, namespace=self.namespace)
            logger.info("cache returns", path=request.url.path, namespace=self.namespace, cached_data=cached_data)
            response.headers[AIO_REDIS_CACHE_HEADER] = self.create_header(cached_data)
            return cached_data
        else:
            return None


async def cacheDependency(request: Request) -> AioRedisCache:
    """Simple FastAPI depency for the dependency injection mechanism that will return the AioRedisCache instance if it is injected in to the ASGI Scope."""
    cache = request.get(AIO_REDIS_CACHE_SCOPE_KEY)
    return cache
