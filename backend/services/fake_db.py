from typing import Dict, List, Optional
from models.category import Category
from models.user import UserToken, UserSession
from models.email import Email
import uuid
import os
from database.db import SessionLocal
from database.models import Category as DBCategory, Email as DBEmail

# In-memory stores
user_sessions: Dict[str, UserSession] = {}  # session_id -> UserSession
categories: List[Category] = []
emails: List[Email] = []
_email_id_counter = 1

# Gmail watch management
def setup_gmail_watch_for_user(email: str, access_token: str, refresh_token: str) -> Optional[str]:
    """
    Set up Gmail watch for a user and return the history ID
    This should be called when a user first connects their Gmail
    """
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        
        # Create credentials
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,
            client_secret=None
        )
        
        # Build Gmail service
        service = build('gmail', 'v1', credentials=creds)
        
        # Get current profile to get the history ID
        profile = service.users().getProfile(userId='me').execute()
        current_history_id = profile.get('historyId')
        
        # Set up Gmail watch
        topic_name = os.getenv("GMAIL_PUBSUB_TOPIC")
        if not topic_name:
            print("Warning: GMAIL_PUBSUB_TOPIC not set, skipping watch setup")
            return current_history_id
        
        request_body = {
            "topicName": topic_name,
            "labelIds": ["INBOX"],
            "labelFilterAction": "include"
        }
        
        watch_response = service.users().watch(userId='me', body=request_body).execute()
        print(f"Gmail watch setup for {email}: {watch_response}")
        
        return current_history_id
        
    except Exception as e:
        print(f"Error setting up Gmail watch for {email}: {e}")
        return None

# User session management
def create_user_session(primary_email: str, access_token: str, refresh_token: Optional[str] = None, history_id: Optional[str] = None) -> str:
    session_id = str(uuid.uuid4())
    primary_account = UserToken(
        email=primary_email,
        access_token=access_token,
        refresh_token=refresh_token,
        history_id=history_id
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

def add_account_to_session(session_id: str, email: str, access_token: str, refresh_token: Optional[str] = None, history_id: Optional[str] = None) -> bool:
    session = user_sessions.get(session_id)
    if not session:
        return False
    
    # Check if account already exists
    for account in session.accounts:
        if account.email == email:
            # Update existing account tokens
            account.access_token = access_token
            account.refresh_token = refresh_token
            if history_id is not None:
                account.history_id = history_id
            print(f"Updated tokens for {email} in session {session_id}")
            return True
    
    # Add new account
    new_account = UserToken(
        email=email,
        access_token=access_token,
        refresh_token=refresh_token,
        history_id=history_id
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

def get_history_id_by_email(email: str) -> Optional[str]:
    for session in user_sessions.values():
        for account in session.accounts:
            if account.email == email:
                return account.history_id
    return None

def set_history_id_by_email(email: str, history_id: str) -> bool:
    for session in user_sessions.values():
        for account in session.accounts:
            if account.email == email:
                account.history_id = history_id
                print(f"Set history_id for {email} to {history_id}")
                return True
    return False

# Category management (SQLAlchemy)
def add_category(category):
    db = SessionLocal()
    db_category = DBCategory(
        name=category.name,
        description=category.description,
        session_id=category.session_id
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    db.close()
    return db_category

def get_categories_by_session(session_id: str):
    db = SessionLocal()
    cats = db.query(DBCategory).filter(DBCategory.session_id == session_id).all()
    db.close()
    return cats

def save_email(email):
    db = SessionLocal()
    db_email = DBEmail(
        subject=email.subject,
        from_email=email.from_email,
        category_id=email.category_id,
        summary=email.summary,
        raw=email.raw,
        user_email=email.user_email,
        gmail_id=email.gmail_id
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    db.close()
    return db_email

def get_emails_by_user_and_category(user_email: str, category_id: int):
    db = SessionLocal()
    emails = db.query(DBEmail).filter(DBEmail.user_email == user_email, DBEmail.category_id == category_id).all()
    db.close()
    return emails

def email_exists(user_email: str, gmail_id: str) -> bool:
    return any(e for e in emails if e.user_email == user_email and e.gmail_id == gmail_id) 