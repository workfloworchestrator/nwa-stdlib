from unittest import mock

from nwastdlib.asyncio import gather_nice_sync


async def test_gather_nice_sync_different_types():
    # Test a variety of different arguments. (You would/should not call a function like this, this is just to test)
    mock_function = mock.MagicMock()

    await gather_nice_sync(
        mock_function,
        [
            1,
            ("foo", "bar"),
            {4, 5},
        ],
    )

    def sortkey(x):
        return str(x)

    assert sorted(mock_function.call_args_list, key=sortkey) == sorted(
        [
            mock.call(1),
            mock.call("foo", "bar"),
            mock.call(4, 5),
        ],
        key=sortkey,
    )


async def test_gather_nice_sync_set():
    # Test that a set of arguments works
    mock_function = mock.MagicMock()

    await gather_nice_sync(mock_function, {"foo", "bar", "baz"})

    assert sorted(mock_function.call_args_list) == sorted(
        [
            mock.call("foo"),
            mock.call("bar"),
            mock.call("baz"),
        ]
    )


async def test_gather_nice_sync_returnvalue():
    # Test that the correct returnvalues are returned
    def mock_function(value1, value2):
        return value1 + value2

    result = await gather_nice_sync(mock_function, [(1, 1), (2, 2)])

    assert result == [2, 4]
