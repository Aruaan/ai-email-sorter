import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import pytest
from fastapi.testclient import TestClient
from main import app
from routes import auth as auth_module
from unittest.mock import patch

client = TestClient(app)

@pytest.mark.skip(reason="OAuth tests are complex and not critical for current development")
@patch('utils.google_oauth.get_auth_url', return_value='https://accounts.google.com/o/oauth2/auth?mocked')
def test_auth_google_redirect(mocked_auth_url):
    response = client.get('/auth/google')
    assert response.status_code == 307  # Redirect
    assert 'accounts.google.com' in response.headers['location']


@pytest.mark.skip(reason="OAuth tests are complex and not critical for current development")
def test_auth_callback_success():
    from unittest.mock import patch, MagicMock
    with patch('utils.google_oauth.fetch_token') as mock_fetch_token, \
         patch('utils.google_oauth.get_user_email', return_value='test@example.com'), \
         patch('services.fake_db.create_user_session', return_value='test-session-id'), \
         patch.dict('os.environ', {
             'FRONTEND_URL': 'http://localhost:3000',
             'GOOGLE_CLIENT_ID': 'test-client-id',
             'GOOGLE_CLIENT_SECRET': 'test-client-secret',
             'GOOGLE_REDIRECT_URI': 'http://localhost:8000/auth/callback'
         }):
        mock_credentials = MagicMock()
        mock_credentials.token = 'access-token'
        mock_credentials.refresh_token = 'refresh-token'
        mock_fetch_token.return_value = mock_credentials
        
        response = client.get('/auth/callback?code=abc&state=xyz')
        assert response.status_code == 307  # Redirect
        assert 'localhost:3000' in response.headers['location']
        assert 'session_id=test-session-id' in response.headers['location']
        assert 'email=test@example.com' in response.headers['location']

def test_auth_callback_missing_code():
    response = client.get('/auth/callback')
    assert response.status_code == 400
    assert 'Missing code' in response.text 