import pytest
from unittest.mock import patch, MagicMock
from backend.services import gmail_processor
from backend.models.user import UserToken
from backend.models.category import Category
import uuid

@pytest.fixture
def user_token():
    return UserToken(email='a@b.com', access_token='tok', refresh_token='ref', history_id='h')

@pytest.fixture
def categories():
    cat_id = uuid.uuid4()
    return [Category(id=cat_id, name='Work', description='desc', session_id='sessid')]

def test_summarize_email():
    with patch.object(gmail_processor.client.chat.completions, 'create') as mock_create:
        mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content='Summary'))])
        summary = gmail_processor.summarize_email('Sub', 'a@b.com', 'b@b.com', 'Body', [])
        assert summary == 'Summary'

def test_classify_email():
    with patch.object(gmail_processor.client.chat.completions, 'create') as mock_create:
        mock_create.return_value = MagicMock(choices=[MagicMock(message=MagicMock(content='Work'))])
        cat_id = uuid.uuid4()
        cat = Category(id=cat_id, name='Work', description='desc', session_id='sessid')
        result = gmail_processor.classify_email('Body', [cat])
        assert result == cat_id

def test_archive_gmail_message():
    service = MagicMock()
    gmail_processor.archive_gmail_message(service, 'gid')
    service.users().messages().modify.assert_called()

def test_process_user_emails_no_categories(user_token):
    with patch('backend.services.gmail_processor.Credentials'), \
         patch('backend.services.gmail_processor.build'), \
         patch('backend.services.gmail_processor.save_email'), \
         patch('backend.services.gmail_processor.get_latest_history_id', return_value='h'), \
         patch('backend.services.session_db.set_history_id_by_email'):
        result = gmail_processor.process_user_emails(user_token, [], max_emails=2, last_history_id='h')
        assert result == []

def test_process_user_emails_no_last_history_id(user_token, categories):
    with patch('backend.services.gmail_processor.Credentials'), \
         patch('backend.services.gmail_processor.build'), \
         patch('backend.services.gmail_processor.save_email'), \
         patch('backend.services.gmail_processor.get_latest_history_id', return_value='h'), \
         patch('backend.services.session_db.set_history_id_by_email') as mock_set:
        result = gmail_processor.process_user_emails(user_token, categories, max_emails=2, last_history_id='')
        mock_set.assert_called()
        assert result == [] 