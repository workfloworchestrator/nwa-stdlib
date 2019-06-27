from nwastdlib.url import URL


def test_url():
    base_url = URL("http://example.org/")

    assert "http://example.org/" == base_url
    assert "URL('http://example.org/')" == repr(base_url)

    assert base_url / "api" == base_url / "/api"

    api_url = base_url / "api"
    assert "http://example.org/api" == api_url

    url = api_url / "ip" / "address" // {"version": 4}
    assert "http://example.org/api/ip/address?version=4" == url

    # paths don't need to be strings
    url = api_url / 1 / 2 / 3
    assert "http://example.org/api/1/2/3" == url

    # query string properly url encoded?
    url = api_url // {"query": ' "%-.<>\\^_`{|}~'}
    assert "http://example.org/api?query=+%22%25-.%3C%3E%5C%5E_%60%7B%7C%7D~" == url
