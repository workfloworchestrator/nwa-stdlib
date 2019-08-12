from nwastdlib.ex import show_ex


def test_show_ex():
    try:
        raise Exception("Test exception")
    except Exception as e:
        ex_string = show_ex(e)

    assert 'Exception: Test exception\n  File "' in ex_string
