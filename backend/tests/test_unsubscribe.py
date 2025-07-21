import pytest
from backend.utils import unsubscribe
from backend.models.email import Email
from unittest.mock import patch, MagicMock
import uuid

@pytest.fixture
def email_obj():
    return Email(id=uuid.uuid4(), subject='S', from_email='a@b.com', category_id=uuid.uuid4(), summary='s', raw='List-Unsubscribe: <http://unsub>', user_email='a@b.com', gmail_id='gid', headers={'List-Unsubscribe': '<http://unsub>'})

def test_extract_unsubscribe_links(email_obj):
    links = unsubscribe.extract_unsubscribe_links(email_obj)
    assert 'http://unsub' in links

def test_extract_unsubscribe_links_html():
    email = Email(id=uuid.uuid4(), subject='S', from_email='a@b.com', category_id=uuid.uuid4(), summary='s', raw='<html><a href="http://unsub">Unsubscribe</a></html>', user_email='a@b.com', gmail_id='gid', headers={})
    links = unsubscribe.extract_unsubscribe_links(email)
    assert 'http://unsub' in links

def test_batch_unsubscribe_worker():
    with patch('backend.services.unsubscribe_worker.unsubscribe_link_worker_async', return_value={"success": True, "link": "http://unsub"}):
        from backend.services.unsubscribe_worker import batch_unsubscribe_worker_async
        import asyncio
        results = asyncio.run(batch_unsubscribe_worker_async(["http://unsub"], user_email="a@b.com"))
        assert results[0]['success'] is True
        assert results[0]['link'] == 'http://unsub' 