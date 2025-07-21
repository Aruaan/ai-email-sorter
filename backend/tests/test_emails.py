import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, MagicMock
import uuid
import json

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_list_emails_for_account(client):
    with patch('backend.services.session_db.get_session_accounts') as mock_acc, \
         patch('backend.services.session_db.get_emails_by_user_and_category') as mock_get:
        mock_acc.return_value = [MagicMock(email='a@b.com')]
        mock_get.return_value = [MagicMock(id=uuid.uuid4(), subject='Sub', from_email='a@b.com', category_id=uuid.uuid4(), summary='sum', raw='raw', user_email='a@b.com', gmail_id='gid')]
        resp = client.get('/emails/?session_id=sessid&category_id=catid&user_email=a@b.com')
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

def test_list_emails_all_accounts(client):
    with patch('backend.services.session_db.get_session_accounts') as mock_acc, \
         patch('backend.services.session_db.get_emails_by_user_and_category') as mock_get:
        mock_acc.return_value = [MagicMock(email='a@b.com'), MagicMock(email='b@b.com')]
        mock_get.side_effect = [[MagicMock(id=uuid.uuid4(), subject='S1', from_email='a@b.com', category_id=uuid.uuid4(), summary='s', raw='r', user_email='a@b.com', gmail_id='g')], []]
        resp = client.get('/emails/?session_id=sessid&category_id=catid')
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

def test_delete_emails(client):
    with patch('backend.database.db.SessionLocal') as mock_db:
        db = MagicMock()
        mock_db.return_value = db
        db.query().filter().first.return_value = MagicMock()
        resp = client.request("DELETE", '/emails/', json=[str(uuid.uuid4()), str(uuid.uuid4())])
        assert resp.status_code == 200
        assert 'deleted_count' in resp.json()

def test_unsubscribe_from_emails(client):
    with patch('backend.database.db.SessionLocal') as mock_db, \
         patch('backend.utils.unsubscribe.extract_unsubscribe_links', return_value=["http://unsub"]):
        db = MagicMock()
        mock_db.return_value = db
        db.query().filter().first.return_value = MagicMock(id=uuid.uuid4(), subject='S', from_email='a@b.com', category_id=uuid.uuid4(), summary='s', raw='r', user_email='a@b.com', gmail_id='g', headers={})
        resp = client.post('/emails/unsubscribe', json=[str(uuid.uuid4())])
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

def test_ai_unsubscribe_from_links(client):
    with patch('backend.routes.emails.batch_unsubscribe_worker', return_value=[{"success": True, "link": "http://unsub"}]):
        resp = client.post('/emails/unsubscribe/ai', json={"unsubscribe_links": ["http://unsub"], "user_email": "a@b.com"})
        assert resp.status_code == 200
        assert resp.json()['results'][0]['success'] in [True, 'True'] 