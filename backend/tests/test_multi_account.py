import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from fastapi.testclient import TestClient
from main import app
from services.fake_db import create_user_session, add_account_to_session, get_user_session, set_primary_account
from models.user import UserToken
from unittest.mock import patch

client = TestClient(app)

def test_create_user_session():
    session_id = create_user_session("test@example.com", "access_token", "refresh_token")
    assert session_id is not None
    assert len(session_id) > 0
    
    session = get_user_session(session_id)
    assert session is not None
    assert session.primary_account == "test@example.com"
    assert len(session.accounts) == 1
    assert session.accounts[0].email == "test@example.com"

def test_add_account_to_session():
    session_id = create_user_session("primary@example.com", "access_token1", "refresh_token1")
    
    # Add second account
    success = add_account_to_session(session_id, "secondary@example.com", "access_token2", "refresh_token2")
    assert success is True
    
    session = get_user_session(session_id)
    assert session is not None
    if session is not None:  # Type guard for linter
        assert len(session.accounts) == 2
        assert any(acc.email == "secondary@example.com" for acc in session.accounts)
        # Primary account should still be the original one
        assert session.primary_account == "primary@example.com"

def test_set_primary_account():
    session_id = create_user_session("primary@example.com", "access_token1", "refresh_token1")
    add_account_to_session(session_id, "secondary@example.com", "access_token2", "refresh_token2")
    
    # Set secondary as primary
    success = set_primary_account(session_id, "secondary@example.com")
    assert success is True
    
    session = get_user_session(session_id)
    assert session is not None
    if session is not None:  # Type guard for linter
        assert session.primary_account == "secondary@example.com"

def test_session_info_endpoint():
    with patch('routes.auth.get_user_session') as mock_get_session:
        mock_session = type('MockSession', (), {
            'session_id': 'test-session',
            'accounts': [
                UserToken(email='test1@example.com', access_token='token1'),
                UserToken(email='test2@example.com', access_token='token2')
            ],
            'primary_account': 'test1@example.com'
        })()
        mock_get_session.return_value = mock_session
        
        response = client.get("/auth/session/test-session")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
        assert len(data["accounts"]) == 2
        assert data["primary_account"] == "test1@example.com"

def test_set_primary_account_endpoint():
    with patch('routes.auth.set_primary_account', return_value=True):
        response = client.post("/auth/session/test-session/primary?email=new@example.com")
        assert response.status_code == 200
        assert response.json()["message"] == "Primary account set to new@example.com"

def test_get_session_accounts_endpoint():
    with patch('main.get_session_accounts') as mock_get_accounts:
        mock_accounts = [
            UserToken(email='test1@example.com', access_token='token1'),
            UserToken(email='test2@example.com', access_token='token2')
        ]
        mock_get_accounts.return_value = mock_accounts
        
        response = client.get("/dev/session/test-session/accounts")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session"
        assert len(data["accounts"]) == 2 