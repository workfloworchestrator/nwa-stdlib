import requests
import requests_mock
from flask_testing import TestCase

from nwastdlib.oauth.oauth_credentials import obtain_client_credentials_token, AUTH_RESOURCE_SERVER, \
    add_client_credentials_token_header, refresh_client_credentials_token
from nwastdlib.test.utils import create_test_app

OAUTH2_TOKEN_URL = 'http://authz-server/oauth/token'


class TestOAuthCredentials(TestCase):
    def create_app(self):
        app = create_test_app()
        return app

    def tearDown(self):
        requests.Session().close()

    @requests_mock.Mocker()
    def test_client_credentials_token_flow(self, m):
        json = {"access_token": "token", "token_type": "bearer", "expires_in": 15498128,
                "scope": "read  write  admin"}
        m.post(OAUTH2_TOKEN_URL, json=json)
        obtain_client_credentials_token(self.app, OAUTH2_TOKEN_URL, 'client_id', 'secret')
        self.assertEqual(self.app.config[AUTH_RESOURCE_SERVER]['access_token'], 'token')

        client = add_client_credentials_token_header({})
        self.assertEqual('bearer token', client.request_headers['Authorization'])

        json['access_token'] = 'new_token'
        m.post(OAUTH2_TOKEN_URL, json=json)

        refresh_client_credentials_token()
        self.assertEqual(self.app.config[AUTH_RESOURCE_SERVER]['access_token'], 'new_token')