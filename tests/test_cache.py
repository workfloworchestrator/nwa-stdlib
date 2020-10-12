import pickle  # noqa: S403
import unittest
from unittest.mock import patch

import fakeredis

from nwastdlib import Either
from nwastdlib.cache import cached_result, read_object, write_object

TEST_OBJECT_1 = ("a", 2, 3.0)
TEST_OBJECT_2 = ("b", 4, 12.9)


class TestObjectCache(unittest.TestCase):
    def setUp(self):
        self.redis = fakeredis.FakeStrictRedis()
        pickled = pickle.dumps(TEST_OBJECT_1)
        self.redis.set("test_read_1", pickled)
        self.pool = Either.Right(self.redis)

    def test_write_object(self):
        key1 = "test_write_1"
        write_object(self.pool, key1, TEST_OBJECT_1, 300)
        self.assertTrue(self.redis.exists(key1))

    @patch("nwastdlib.cache.request", spec={})  # Spec because of https://github.com/testing-cabal/mock/issues/490
    def test_read_object(self, request):
        request.headers = {}
        obj = read_object(self.pool, "test_read_1")
        self.assertTupleEqual(obj, TEST_OBJECT_1)

    @patch("nwastdlib.cache.request", spec={})  # Spec because of https://github.com/testing-cabal/mock/issues/490
    def test_cached_result(self, request):
        request.headers = {}

        @cached_result(self.pool, expiry=500)
        def test_func(test_id, test_kwarg=21):
            return TEST_OBJECT_2

        test_func("myid")
        self.assertTrue(self.redis.exists("test_func:myid"))
        test_func("otherid", test_kwarg=100)
        self.assertTrue(self.redis.exists("test_func:otherid:100"))
        ttl_lower_than_500 = self.redis.ttl("test_func:myid") <= 500
        self.assertTrue(ttl_lower_than_500)
        self.assertTupleEqual(read_object(self.pool, "test_func:myid"), test_func("myid"))

    @patch("nwastdlib.cache.request", spec={})  # Spec because of https://github.com/testing-cabal/mock/issues/490
    def test_cached_result_prefix(self, request):
        request.headers = {}

        @cached_result(self.pool, prefix="my_prefix")
        def not_this_prefix():
            return TEST_OBJECT_1

        not_this_prefix()
        self.assertTrue(self.redis.exists("my_prefix"))

    @patch("nwastdlib.cache.request", spec={})  # Spec because of https://github.com/testing-cabal/mock/issues/490
    def test_cached_result_skipped_args(self, request):
        request.headers = {}

        @cached_result(self.pool)
        def skipped_args(dict_arg):
            return dict_arg

        skipped_args({"a": 1, "b": 2})
        self.assertTrue(self.redis.exists("skipped_args"))
        self.assertDictEqual(read_object(self.pool, "skipped_args"), {"a": 1, "b": 2})
