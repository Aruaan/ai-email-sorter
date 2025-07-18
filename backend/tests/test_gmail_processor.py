import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from services.gmail_processor import process_user_emails
from models.user import UserToken
from models.category import Category
from unittest.mock import patch, MagicMock


def test_process_user_emails():
    user_token = UserToken(email="test@example.com", access_token="token", refresh_token="refresh")
    categories = [Category(id=1, name="Work", description="Work stuff", user_email="test@example.com")]

    # Patch Gmail API and AI functions
    with patch('services.gmail_processor.build') as mock_build, \
         patch('services.gmail_processor.Credentials') as mock_creds, \
         patch('services.gmail_processor.classify_email', return_value=1) as mock_classify, \
         patch('services.gmail_processor.summarize_email', return_value="summary") as mock_summarize:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }
        mock_service.users().messages().get().execute.side_effect = [
            {
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
            },
            {
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': 'Test2'},
                        {'name': 'From', 'value': 'sender2@example.com'}
                    ],
                    'parts': []
                },
                'snippet': 'snippet2'
            }
        ]
        result = process_user_emails(user_token, categories)
        assert isinstance(result, list)
        assert len(result) == 2
        for email in result:
            assert 'subject' in email
            assert 'from' in email
            assert 'category_id' in email
            assert 'summary' in email
            assert 'raw' in email
        mock_classify.assert_called()
        mock_summarize.assert_called()


def test_process_user_emails_with_dummy_data():
    user_token = UserToken(email="test@example.com", access_token="token", refresh_token="refresh")
    categories = [Category(id=1, name="Work", description="Work stuff", user_email="test@example.com")]

    # Patch Gmail API and AI functions
    with patch('services.gmail_processor.build') as mock_build, \
         patch('services.gmail_processor.Credentials') as mock_creds, \
         patch('services.gmail_processor.classify_email', return_value=1) as mock_classify, \
         patch('services.gmail_processor.summarize_email', return_value="summary") as mock_summarize:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': 'msg1'}, {'id': 'msg2'}]
        }
        mock_service.users().messages().get().execute.side_effect = [
            {
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
            },
            {
                'payload': {
                    'headers': [
                        {'name': 'Subject', 'value': 'Test2'},
                        {'name': 'From', 'value': 'sender2@example.com'}
                    ],
                    'parts': []
                },
                'snippet': 'snippet2'
            }
        ]
        result = process_user_emails(user_token, categories)
        assert isinstance(result, list)
        assert len(result) == 2
        for email in result:
            assert 'subject' in email
            assert 'from' in email
            assert 'category_id' in email
            assert 'summary' in email
            assert 'raw' in email
        mock_classify.assert_called()
        mock_summarize.assert_called() 