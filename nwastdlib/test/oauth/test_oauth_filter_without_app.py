import unittest

from nwastdlib.oauth.oauth_filter import OAuthFilter


class TestOauthFilterWithoutApp(unittest.TestCase):
    def test_get_current_user(self):
        res = OAuthFilter.current_user()
        self.assertEqual(None, res)
