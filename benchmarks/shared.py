import asyncio
import random
import time

DICT_SIZE = 10000  # around 80Kb
REPEAT = 10000


def timeit(func):
    async def process(func, *args, **params):
        if asyncio.iscoroutinefunction(func):
            # print('this function is a coroutine: {}'.format(func.__name__))
            return await func(*args, **params)

        # print('this is not a coroutine')
        return func(*args, **params)

    async def helper(*args, **params):
        print(f"Repeat {func.__name__} {REPEAT} times:")  # noqa: T201
        start = time.time()
        result = await process(func, *args, **params)
        total_time = time.time() - start
        print(f"Total time (seconds)={total_time}, time per read (seconds)={total_time / REPEAT}")  # noqa: T201
        return result

    return helper


async def get_big_dict():
    result = {}
    for i in range(0, DICT_SIZE):
        result[f"{i}"] = random.randint(0, DICT_SIZE * 100)  # noqa: S311
    return result
