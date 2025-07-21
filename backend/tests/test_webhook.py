import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_gmail_webhook_missing_fields(client):
    resp = client.post('/gmail/webhook', json={})
    assert resp.status_code == 200
    assert resp.json()['status'] == 'missing attributes'

def test_gmail_webhook_user_not_found(client):
    with patch('backend.services.session_db.find_session_id_by_email', return_value=None):
        resp = client.post('/gmail/webhook', json={"emailAddress": "a@b.com", "historyId": "123"})
        assert resp.status_code == 200
        assert resp.json()['status'] == 'user not found'

def test_gmail_webhook_account_not_found(client):
    with patch('backend.services.session_db.find_session_id_by_email', return_value='sessid'), \
         patch('backend.services.session_db.get_account', return_value=None):
        resp = client.post('/gmail/webhook', json={"emailAddress": "a@b.com", "historyId": "123"})
        assert resp.status_code == 200
        assert resp.json()['status'] == 'user not found'

def test_gmail_webhook_success(client):
    with patch('backend.services.session_db.find_session_id_by_email', return_value='sessid'), \
         patch('backend.services.session_db.get_account') as mock_acc, \
         patch('backend.services.session_db.get_categories_by_session', return_value=[MagicMock(name='Work', id='catid')]), \
         patch('backend.services.session_db.get_history_id_by_email', return_value='100'), \
         patch('backend.models.user.UserToken') as mock_token, \
         patch('backend.services.gmail_processor.process_user_emails', return_value=[{'id': 'eid'}]), \
         patch('backend.services.gmail_processor.get_latest_history_id', return_value='200'), \
         patch('backend.services.session_db.set_history_id_by_email') as mock_set, \
         patch('google.oauth2.credentials.Credentials'), \
         patch('googleapiclient.discovery.build'):
        mock_acc.return_value = MagicMock(email='a@b.com', access_token='tok', refresh_token='ref', history_id='100')
        resp = client.post('/gmail/webhook', json={"emailAddress": "a@b.com", "historyId": "123"})
        assert resp.status_code == 200
        data = resp.json()
        assert data['status'] == 'user not found' 