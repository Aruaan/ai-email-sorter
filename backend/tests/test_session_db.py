import pytest
from services.session_db import (
    create_session, add_account_to_session, get_session, get_session_accounts,
    set_primary_account, get_primary_account, get_account, get_account_by_email,
    set_history_id_by_email, get_history_id_by_email, find_session_id_by_email
)

def test_create_and_retrieve_session():
    session_id = "test-session-1"
    primary = "user1@example.com"
    accounts = [{"email": primary, "access_token": "tok1"}]
    create_session(session_id, primary, accounts)
    session = get_session(session_id)
    assert session.id == session_id
    assert session.primary_account == primary
    assert any(acc.email == primary for acc in session.accounts)

def test_add_account_to_session_and_get():
    session_id = "test-session-2"
    create_session(session_id, "user2@example.com", [{"email": "user2@example.com", "access_token": "tok2"}])
    add_account_to_session(session_id, "user3@example.com", "tok3")
    accounts = get_session_accounts(session_id)
    assert any(acc.email == "user3@example.com" for acc in accounts)

def test_set_and_get_primary_account():
    session_id = "test-session-3"
    create_session(session_id, "user4@example.com", [{"email": "user4@example.com", "access_token": "tok4"}])
    add_account_to_session(session_id, "user5@example.com", "tok5")
    set_primary_account(session_id, "user5@example.com")
    assert get_primary_account(session_id) == "user5@example.com"

def test_get_account_by_email_and_history_id():
    session_id = "test-session-4"
    email = "user6@example.com"
    create_session(session_id, email, [{"email": email, "access_token": "tok6"}])
    set_history_id_by_email(email, "hist123")
    assert get_history_id_by_email(email) == "hist123"
    assert find_session_id_by_email(email) == session_id
