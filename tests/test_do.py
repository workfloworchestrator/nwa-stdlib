import unittest
from nwastdlib import Either, do, mreturn


@do(Either)
def api(value):
    val = yield Either.Right(value) if value else Either.Left("None")
    mreturn({"key": val})


# To understand @do read https://docs.python.org/3/reference/expressions.html#grammar-token-yield_atom
# Or debug the test and follow the flow and Exception raising / handling in @do
class TestDo(unittest.TestCase):
    def test_do_mreturn_right(self):
        new_state = api("test")
        self.assertTrue(new_state.isright())
        self.assertDictEqual({"key": "test"}, new_state.value)

    def test_do_mreturn_left(self):
        new_state = api(None)
        self.assertTrue(new_state.isleft())
        self.assertEqual("None", new_state.value)
