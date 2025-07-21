import pytest
from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, MagicMock

@pytest.fixture(scope="module")
def client():
    return TestClient(app)

def test_create_category(client):
    with patch('backend.services.session_db.add_category') as mock_add:
        mock_add.return_value = MagicMock(id='catid', name='Work', description='desc', session_id='sessid')
        resp = client.post('/categories/', json={"name": "Work", "description": "desc", "session_id": "sessid"})
        assert resp.status_code == 200
        data = resp.json()
        assert data['name'] == 'Work'
        assert data['description'] == 'desc'
        assert data['session_id'] == 'sessid'

def test_list_categories(client):
    with patch('backend.services.session_db.get_categories_by_session') as mock_get:
        mock_get.return_value = [MagicMock(id='catid', name='Work', description='desc', session_id='sessid')]
        resp = client.get('/categories/?session_id=sessid')
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]['name'] == 'Work'

def test_update_category_name_with_emails(client):
    # Simulate category with emails (should block rename)
    with patch('backend.database.db.SessionLocal') as mock_db:
        db = MagicMock()
        mock_db.return_value = db
        cat = MagicMock(id='catid', name='Work', description='desc', session_id='sessid')
        db.query().filter().first.return_value = cat
        db.query().filter().count.return_value = 2  # 2 emails in category
        resp = client.put('/categories/catid', json={"name": "NewName"})
        assert resp.status_code == 200
        assert 'Cannot rename category' in resp.json()['error']

def test_update_category_description(client):
    with patch('backend.database.db.SessionLocal') as mock_db:
        db = MagicMock()
        mock_db.return_value = db
        cat = MagicMock(id='catid', name='Work', description='desc', session_id='sessid')
        db.query().filter().first.return_value = cat
        db.query().filter().count.return_value = 0
        resp = client.put('/categories/catid', json={"description": "newdesc"})
        assert resp.status_code == 200
        assert resp.json()['category']['description'] == 'newdesc' 