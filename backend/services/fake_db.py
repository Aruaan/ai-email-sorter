from typing import Dict, List, Optional
from models.category import Category
from models.user import UserToken, UserSession
from models.email import Email
import uuid

# In-memory stores
user_sessions: Dict[str, UserSession] = {}  # session_id -> UserSession
categories: List[Category] = []
emails: List[Email] = []
_email_id_counter = 1

# User session management
def create_user_session(primary_email: str, access_token: str, refresh_token: Optional[str] = None) -> str:
    session_id = str(uuid.uuid4())
    primary_account = UserToken(
        email=primary_email,
        access_token=access_token,
        refresh_token=refresh_token
    )
    user_session = UserSession(
        session_id=session_id,
        accounts=[primary_account],
        primary_account=primary_email
    )
    user_sessions[session_id] = user_session
    print(f"Created session {session_id} for {primary_email}")
    return session_id

def get_user_session(session_id: str) -> Optional[UserSession]:
    return user_sessions.get(session_id)

def add_account_to_session(session_id: str, email: str, access_token: str, refresh_token: Optional[str] = None) -> bool:
    session = user_sessions.get(session_id)
    if not session:
        return False
    
    # Check if account already exists
    for account in session.accounts:
        if account.email == email:
            # Update existing account tokens
            account.access_token = access_token
            account.refresh_token = refresh_token
            print(f"Updated tokens for {email} in session {session_id}")
            return True
    
    # Add new account
    new_account = UserToken(
        email=email,
        access_token=access_token,
        refresh_token=refresh_token
    )
    session.accounts.append(new_account)
    print(f"Added account {email} to session {session_id}")
    return True

def get_user_token(session_id: str, email: str) -> Optional[UserToken]:
    session = user_sessions.get(session_id)
    if not session:
        return None
    
    for account in session.accounts:
        if account.email == email:
            return account
    return None

def get_primary_account(session_id: str) -> Optional[UserToken]:
    session = user_sessions.get(session_id)
    if not session:
        return None
    
    return get_user_token(session_id, session.primary_account)

def set_primary_account(session_id: str, email: str) -> bool:
    session = user_sessions.get(session_id)
    if not session:
        return False
    
    # Verify the account exists in the session
    for account in session.accounts:
        if account.email == email:
            session.primary_account = email
            print(f"Set primary account to {email} for session {session_id}")
            return True
    return False

def get_session_accounts(session_id: str) -> List[UserToken]:
    session = user_sessions.get(session_id)
    if not session:
        return []
    return session.accounts

# Legacy support for existing single-user functions
def save_user_token(user_token: UserToken):
    # Create a new session for backward compatibility
    session_id = create_user_session(
        user_token.email, 
        user_token.access_token, 
        user_token.refresh_token
    )
    print(f"Legacy save_user_token: Created session {session_id} for {user_token.email}")

def get_user_token_by_email(email: str) -> Optional[UserToken]:
    # Search through all sessions for the email
    for session in user_sessions.values():
        for account in session.accounts:
            if account.email == email:
                return account
    return None

# Category management
def add_category(category: Category):
    categories.append(category)

def get_categories_by_user(email: str) -> List[Category]:
    return [cat for cat in categories if cat.user_email == email]

def save_email(email: Email):
    global _email_id_counter
    email.id = _email_id_counter
    _email_id_counter += 1
    emails.append(email)

def get_emails_by_user_and_category(user_email: str, category_id: int) -> List[Email]:
    return [e for e in emails if e.user_email == user_email and e.category_id == category_id]

def email_exists(user_email: str, gmail_id: str) -> bool:
    return any(e for e in emails if e.user_email == user_email and e.gmail_id == gmail_id) 