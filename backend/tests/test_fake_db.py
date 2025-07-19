from services.fake_db import (
    create_user_session, get_user_session, add_account_to_session,
    get_user_token, get_primary_account, set_primary_account,
    get_session_accounts, get_user_token_by_email, get_history_id_by_email, set_history_id_by_email
)

def test_create_and_get_user_session():
    session_id = create_user_session("test@example.com", "token", "refresh", "history1")
    session = get_user_session(session_id)
    assert session is not None
    assert hasattr(session, "primary_account")
    assert session.primary_account == "test@example.com"
    assert hasattr(session, "accounts")
    assert session.accounts[0].email == "test@example.com"
    assert session.accounts[0].history_id == "history1"

def test_add_account_to_session_and_get_token():
    session_id = create_user_session("primary@example.com", "token1", "refresh1")
    add_account_to_session(session_id, "secondary@example.com", "token2", "refresh2", "history2")
    session = get_user_session(session_id)
    assert session is not None
    assert hasattr(session, "accounts")
    assert len(session.accounts) == 2
    token = get_user_token(session_id, "secondary@example.com")
    assert token is not None
    assert hasattr(token, "email")
    assert token.email == "secondary@example.com"
    assert hasattr(token, "history_id")
    assert token.history_id == "history2"

def test_set_and_get_primary_account():
    session_id = create_user_session("primary@example.com", "token1", "refresh1")
    add_account_to_session(session_id, "secondary@example.com", "token2", "refresh2")
    set_primary_account(session_id, "secondary@example.com")
    session = get_user_session(session_id)
    assert session is not None
    assert hasattr(session, "primary_account")
    assert session.primary_account == "secondary@example.com"
    primary_account = get_primary_account(session_id)
    assert primary_account is not None
    assert hasattr(primary_account, "email")
    assert primary_account.email == "secondary@example.com"

def test_get_user_token_by_email_and_history_id():
    session_id = create_user_session("user1@example.com", "token", "refresh", "historyA")
    add_account_to_session(session_id, "user2@example.com", "token2", "refresh2", "historyB")
    token = get_user_token_by_email("user2@example.com")
    assert token is not None
    assert hasattr(token, "email")
    assert token.email == "user2@example.com"
    assert get_history_id_by_email("user2@example.com") == "historyB"
    set_history_id_by_email("user2@example.com", "historyC")
    assert get_history_id_by_email("user2@example.com") == "historyC"