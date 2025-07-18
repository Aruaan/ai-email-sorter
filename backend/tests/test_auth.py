import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import pytest
from fastapi.testclient import TestClient
from main import app
from routes import auth as auth_module
from unittest.mock import patch

client = TestClient(app)

@pytest.mark.skip(reason="Skipping Google OAuth tests for now")
@patch('utils.google_oauth.get_auth_url', return_value='https://accounts.google.com/o/oauth2/auth?mocked')
def test_auth_google_redirect(mocked_auth_url):
    response = client.get('/auth/google')
    assert response.status_code == 307  # Redirect
    assert 'accounts.google.com' in response.headers['location']


def test_auth_callback_success():
    from unittest.mock import patch
    with patch('routes.auth.fetch_token') as mock_fetch_token, \
         patch('routes.auth.get_user_email', return_value='test@example.com'), \
         patch('routes.auth.save_user_token') as mock_save_user_token:
        class DummyCreds:
            token = 'access-token'
            refresh_token = 'refresh-token'
        mock_fetch_token.return_value = DummyCreds()
        response = client.get('/auth/callback?code=abc&state=xyz')
        assert response.status_code == 200
        assert response.json()['message'] == 'Authentication successful'
        assert response.json()['email'] == 'test@example.com'
        mock_save_user_token.assert_called()

def test_auth_callback_missing_code():
    response = client.get('/auth/callback')
    assert response.status_code == 400
    assert 'Missing code' in response.text 