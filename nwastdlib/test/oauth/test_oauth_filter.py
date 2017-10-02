import requests
import requests_mock
import yaml
from flask_testing import TestCase

from nwastdlib.oauth.oauth_filter import OAuthFilter
from nwastdlib.test.utils import create_test_app

ENVIRON_BASE = {'HTTP_AUTHORIZATION': 'bearer test'}

TOKEN_CHECK_URL = 'http://authz-server/token_check'


@requests_mock.Mocker()
class TestOAuthFilter(TestCase):
    def create_app(self):
        app = create_test_app()
        with open('./nwastdlib/test/oauth/security_definitions.yaml') as file:
            security_definitions = yaml.load(file)
            app.before_request(
                OAuthFilter(security_definitions['securityDefinitions'], TOKEN_CHECK_URL, 'coredb', 'secret',
                            ['config']).filter)
            return app

    def tearDown(self):
        requests.Session().close()

    def test_happy_flow_with_custom_admin_scope(self, m):
        self._check(m,
                    json=self._json(['read', 'admin']))

    def test_no_token(self, m):
        self._check(m,
                    environ_base={},
                    response_status_code=401,
                    response_detail='401 Unauthorized: No Authorization token provided')

    def test_invalid_header(self, m):
        self._check(m,
                    environ_base={'HTTP_AUTHORIZATION': 'nope'},
                    response_status_code=401,
                    response_detail='401 Unauthorized: Invalid authorization header: nope')

    def test_invalid_token(self, m):
        self._check(m,
                    status_code=400,
                    response_status_code=401,
                    response_detail='401 Unauthorized: Provided oauth token test is not valid')

    def test_missing_required_operation_scope(self, m):
        self._check(m,
                    json=self._json(['read']),
                    response_status_code=403,
                    response_detail='403 Forbidden: Provided token does not have the required scope(s): {\'admin\'}')

    def test_missing_read_scope(self, m):
        self._check(m,
                    json=self._json(['admin']),
                    response_status_code=403,
                    response_detail='403 Forbidden: Provided token does not have the required scope(s): {\'read\'}')

    def test_whitelisted_endpoints(self, m):
        m.get(TOKEN_CHECK_URL, status_code=500)
        response = self.client.get("/config")
        self.assertEqual(200, response.status_code)

    def test_missing_write_scope_for_write_endpoints(self, m):
        m.get(TOKEN_CHECK_URL, json=self._json(['read']))
        response = self.client.post("/hello", environ_base=ENVIRON_BASE)
        self.assertEqual(403, response.status_code)
        self.assertEqual('403 Forbidden: Provided token does not have the required scope(s): {\'write\'}',
                         response.json['detail'])

    def test_missing_admin_scope_for_delete_endpoints(self, m):
        m.get(TOKEN_CHECK_URL, json=self._json(['write']))
        response = self.client.delete("/hello", environ_base=ENVIRON_BASE)
        self.assertEqual(403, response.status_code)
        self.assertEqual('403 Forbidden: Provided token does not have the required scope(s): {\'admin\'}',
                         response.json['detail'])

    def _check(self, m, json=None, status_code=200, environ_base=ENVIRON_BASE,
               response_status_code=200, response_detail=None):
        m.get(TOKEN_CHECK_URL, json=json, status_code=status_code)
        response = self.client.get("/hello", environ_base=environ_base)

        self.assertEqual(response_status_code, response.status_code)

        if response_status_code != 200:
            self.assertEqual(response_detail, response.json['detail'])
            self.assertEqual(None, OAuthFilter.current_user())
        else:
            user = OAuthFilter.current_user()
            self.assertEqual('john.doe', user['user_name'])

    @staticmethod
    def _json(scopes):
        return {'user_name': 'john.doe', 'aud': ['coredb'], 'scope': scopes}
