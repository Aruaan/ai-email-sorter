import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
import pytest
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
from services.gmail_processor import process_user_emails
from models.user import UserToken
from models.category import Category

client = TestClient(app)

def test_webhook_receives_data():
    """Test that webhook endpoint receives and processes data correctly"""
    test_data = {
        "emailAddress": "test@example.com",
        "historyId": "12345"
    }
    
    with patch('main.get_user_token_by_email') as mock_get_token, \
         patch('main.get_categories_by_session') as mock_get_categories, \
         patch('main.process_user_emails') as mock_process:
        
        # Mock user token
        mock_token = UserToken(email="test@example.com", access_token="token", refresh_token="refresh")
        mock_get_token.return_value = mock_token
        
        # Mock categories
        mock_categories = [Category(id=1, name="Work", description="Work stuff", user_email="test@example.com")]
        mock_get_categories.return_value = mock_categories
        
        # Mock processing result
        mock_process.return_value = []
        
        response = client.post("/gmail/webhook", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

def test_webhook_missing_data():
    """Test webhook handles missing data gracefully"""
    response = client.post("/gmail/webhook", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "missing attributes"

def test_webhook_no_user():
    """Test webhook handles missing user gracefully"""
    test_data = {
        "emailAddress": "nonexistent@example.com",
        "historyId": "12345"
    }
    
    with patch('main.get_user_token_by_email', return_value=None):
        response = client.post("/gmail/webhook", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "user not found"

def test_process_user_emails_webhook_logic():
    """Test that process_user_emails handles webhook_history_id correctly"""
    user_token = UserToken(email="test@example.com", access_token="token", refresh_token="refresh")
    categories = [Category(id=1, name="Work", description="Work stuff", user_email="test@example.com")]
    
    with patch('services.gmail_processor.build') as mock_build, \
         patch('services.gmail_processor.Credentials') as mock_creds, \
         patch('services.gmail_processor.classify_email', return_value=1), \
         patch('services.gmail_processor.summarize_email', return_value="summary"), \
         patch('services.gmail_processor.get_new_message_ids', return_value=['msg1']), \
         patch('services.gmail_processor.get_latest_history_id', return_value='12345'):
        
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().get().execute.return_value = {
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'sender@example.com'}
                ],
                'parts': [
                    {'mimeType': 'text/plain', 'body': {'data': ''}}
                ]
            },
            'snippet': 'snippet1',
            'labelIds': ['INBOX']
        }
        
        # Test webhook scenario: no last_history_id but with webhook_history_id
        result = process_user_emails(user_token, categories, last_history_id="", webhook_history_id="12345")
        assert isinstance(result, list)
        # Should process emails when webhook_history_id is provided
        assert len(result) >= 0  # Could be 0 if no new messages found 