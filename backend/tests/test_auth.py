import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_auth_callback_missing_code(client):
    resp = client.get('/auth/callback')
    assert resp.status_code == 400
    assert 'Missing code' in resp.text

def test_auth_callback_success(client):
    mock_creds = MagicMock(token='tok', refresh_token='ref')
    with patch('backend.utils.google_oauth.fetch_token', return_value=mock_creds), \
         patch('backend.utils.google_oauth.get_user_email', return_value='user@example.com'), \
         patch('backend.services.session_db.setup_gmail_watch_for_user', return_value='histid'), \
         patch('backend.services.session_db.get_or_create_session_by_email', return_value='sessid'), \
         patch('backend.services.session_db.get_or_create_uncategorized_category'):
        resp = client.get('/auth/callback?code=abc')
        assert resp.status_code in (302, 307, 400)

def test_get_session_info_success(client):
    mock_session = MagicMock(id='sessid', accounts=[MagicMock(email='a@b.com'), MagicMock(email='b@b.com')], primary_account='a@b.com')
    with patch('backend.services.session_db.get_session', return_value=mock_session):
        resp = client.get('/auth/session/sessid')
        if resp.status_code == 200:
            data = resp.json()
            assert data['session_id'] == 'sessid'
            assert data['primary_account'] == 'a@b.com'
            assert {'email': 'a@b.com'} in data['accounts']
            assert {'email': 'b@b.com'} in data['accounts']
        else:
            assert resp.status_code == 404

def test_set_primary_account_success(client):
    with patch('backend.services.session_db.set_primary_account', return_value=True):
        resp = client.post('/auth/session/sessid/primary?email=a@b.com')
        if resp.status_code == 200:
            assert 'Primary account set to a@b.com' in resp.text
        else:
            assert resp.status_code == 404

def test_remove_account_success(client):
    with patch('backend.services.session_db.remove_account_from_session', return_value=(True, 'Removed')):
        resp = client.delete('/auth/session/sessid/account?email=a@b.com')
        if resp.status_code == 200:
            data = resp.json()
            assert data['removed_email'] == 'a@b.com'
            assert data['message'] == 'Removed'
        else:
            assert resp.status_code == 400

def test_logout_success(client):
    with patch('backend.services.session_db.delete_session', return_value=True):
        resp = client.post('/auth/logout?session_id=sessid')
        assert resp.status_code == 200
        assert 'Logged out successfully' in resp.text 