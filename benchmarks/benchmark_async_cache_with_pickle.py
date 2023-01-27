# import asyncio
# import random
# import timeit
#
# from redis.asyncio import Redis as AIORedis
# from shared import SIZE
#
# from nwastdlib.asyncio_cache import cached_result
#
# cache: AIORedis = AIORedis(host="127.0.0.1", port=6379)
#
#
# @cached_result(cache, "test-suite", "SECRETNAME", "keyname", expiry_seconds=2000)
# async def big_dict():
#     result = {}
#     for i in range(0, SIZE):
#         result[i] = random.randint(0, SIZE * 100)
#     return result
#
#
# # warm the cache:
# result = await big_dict()
#
# timeit.repeat(await big_dict(), repeat=100)
# asyncio.run()
