import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch

client = TestClient(app)

def test_create_category():
    with patch('routes.categories.add_category') as mock_add_category:
        data = {
            "name": "Work",
            "description": "Work related emails",
            "user_email": "test@example.com"
        }
        response = client.post('/categories/', json=data)
        assert response.status_code == 200
        result = response.json()
        assert result['name'] == data['name']
        assert result['description'] == data['description']
        assert result['user_email'] == data['user_email']
        mock_add_category.assert_called()

def test_list_categories():
    with patch('routes.categories.get_categories_by_user', return_value=[
        {"id": 1, "name": "Work", "description": "Work related emails", "user_email": "test@example.com"}
    ]):
        response = client.get('/categories/?user_email=test@example.com')
        assert response.status_code == 200
        categories = response.json()
        assert isinstance(categories, list)
        assert categories[0]['name'] == "Work" 

def test_create_and_list_category():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    session_id = "cat-session"
    resp = client.post("/categories/", json={"name": "TestCat", "description": "desc", "session_id": session_id})
    assert resp.status_code == 200
    resp2 = client.get(f"/categories/?session_id={session_id}")
    assert any(cat["name"] == "TestCat" for cat in resp2.json()) 