import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from fastapi.testclient import TestClient
from main import app
from unittest.mock import patch, MagicMock
from services.fake_db import emails, save_email, get_emails_by_user_and_category
from models.email import Email

client = TestClient(app)

def test_save_and_get_emails():
    emails.clear()
    email = Email(
        id=0,
        subject="Test Subject",
        from_email="sender@example.com",
        category_id=1,
        summary="summary",
        raw="body",
        user_email="test@example.com",
        gmail_id="gmailid1"
    )
    save_email(email)
    result = get_emails_by_user_and_category("test@example.com", 1)
    assert len(result) == 1
    assert result[0].subject == "Test Subject"
    assert result[0].category_id == 1

def test_emails_api_returns_emails():
    emails.clear()
    email = Email(
        id=0,
        subject="Test Subject",
        from_email="sender@example.com",
        category_id=2,
        summary="summary",
        raw="body",
        user_email="apiuser@example.com",
        gmail_id="gmailid2"
    )
    save_email(email)
    response = client.get("/emails/?user_email=apiuser@example.com&category_id=2")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert data[0]["subject"] == "Test Subject"
    assert data[0]["category_id"] == 2

def test_process_user_emails_stores_and_skips_duplicates():
    from services.gmail_processor import process_user_emails
    from models.user import UserToken
    from models.category import Category
    emails.clear()
    user_token = UserToken(email="dup@example.com", access_token="token", refresh_token="refresh")
    categories = [Category(id=1, name="Work", description="desc", user_email="dup@example.com")]
    with patch('services.gmail_processor.build') as mock_build, \
         patch('services.gmail_processor.Credentials') as mock_creds, \
         patch('services.gmail_processor.classify_email', return_value=1), \
         patch('services.gmail_processor.summarize_email', return_value="summary"):
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg1'}]  # duplicate gmail_id
        }
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
            'snippet': 'snippet1'
        }
        result = process_user_emails(user_token, categories, max_emails=2)
        assert len(result) == 1  # Only one email stored due to duplicate gmail_id
        assert emails[0].gmail_id == 'msg1' 

def test_extract_unsubscribe_links():
    from utils.unsubscribe import extract_unsubscribe_links
    # Email with List-Unsubscribe header and HTML body
    raw = (
        'List-Unsubscribe: <https://unsubscribe.example.com/unsub>\n'
        '<html><body>'
        '<a href="https://unsubscribe.example.com/unsub">Unsubscribe here</a>'
        '<a href="https://other.example.com/keep">Keep</a>'
        'Or visit https://unsubscribe.example.com/unsub2 in your browser.'
        '</body></html>'
    )
    email = Email(
        id=123,
        subject="Test Unsub",
        from_email="sender@example.com",
        category_id=1,
        summary="summary",
        raw=raw,
        user_email="test@example.com",
        gmail_id="gmailid-unsub"
    )
    links = extract_unsubscribe_links(email)
    print("Extracted unsubscribe links:", links)
    assert "https://unsubscribe.example.com/unsub" in links
    assert "https://unsubscribe.example.com/unsub2" in links
    # Should not include unrelated links
    assert all("keep" not in l for l in links) 