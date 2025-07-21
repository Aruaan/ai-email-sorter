import pytest
from unittest.mock import patch, MagicMock
from backend.main import app
from fastapi.testclient import TestClient

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_create_test_session(client):
    with patch('backend.services.session_db.create_session') as mock_create:
        resp = client.post('/dev/test/create-session?email=a@b.com')
        assert resp.status_code == 200
        data = resp.json()
        assert 'session_id' in data
        assert data['email'] == 'a@b.com'

def test_add_test_account(client):
    with patch('backend.services.session_db.add_account_to_session') as mock_add:
        resp = client.post('/dev/test/add-account?session_id=sessid&email=b@b.com')
        assert resp.status_code == 200
        data = resp.json()
        assert data['session_id'] == 'sessid'
        assert data['email'] == 'b@b.com'

def test_get_session_accounts_endpoint(client):
    with patch('backend.main.get_session_accounts') as mock_get:
        mock_get.return_value = [MagicMock(email='a@b.com'), MagicMock(email='b@b.com')]
        resp = client.get('/dev/session/sessid/accounts')
        assert resp.status_code == 200
        data = resp.json()
        emails = [acc['email'] for acc in data['accounts']]
        assert 'a@b.com' in emails
        assert 'b@b.com' in emails

def test_set_primary_account_endpoint(client):
    with patch('backend.services.session_db.set_primary_account', return_value=True):
        resp = client.post('/auth/session/sessid/primary?email=a@b.com')
        if resp.status_code == 200:
            assert 'Primary account set to a@b.com' in resp.text
        else:
            assert resp.status_code == 404

def test_remove_account_endpoint(client):
    with patch('backend.services.session_db.remove_account_from_session', return_value=(True, 'Removed')):
        resp = client.delete('/auth/session/sessid/account?email=a@b.com')
        assert resp.status_code == 200
        data = resp.json()
        assert data['removed_email'] == 'a@b.com'
        assert data['message'] == 'Removed' 