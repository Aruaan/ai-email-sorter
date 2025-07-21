from backend.database.db import SessionLocal
from backend.database.models import Session as DBSession, SessionAccount as DBSessionAccount, Category as DBCategory, Email as DBEmail
from sqlalchemy.orm import joinedload
import json
import os

# Gmail watch management
def setup_gmail_watch_for_user(email: str, access_token: str, refresh_token: str):
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

# Category and Email management
def add_category(category):
    db = SessionLocal()
    db_category = DBCategory(
        id=category.id,
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
    # Convert headers dict to JSON string for SQLite compatibility
    headers_json = json.dumps(email.headers) if email.headers else None
    db_email = DBEmail(
        id=email.id,
        subject=email.subject,
        from_email=email.from_email,
        category_id=email.category_id,
        summary=email.summary,
        raw=email.raw,
        user_email=email.user_email,
        gmail_id=email.gmail_id,
        headers=headers_json  # Save headers as JSON string
    )
    db.add(db_email)
    db.commit()
    db.refresh(db_email)
    db.close()
    return db_email

def get_emails_by_user_and_category(user_email: str, category_id: str):
    db = SessionLocal()
    # Convert string category_id to UUID for proper comparison
    import uuid
    try:
        category_uuid = uuid.UUID(category_id)
        db_emails = db.query(DBEmail).filter(DBEmail.user_email == user_email, DBEmail.category_id == category_uuid).all()
    except ValueError:
        # If category_id is not a valid UUID, return empty list
        db_emails = []
    db.close()
    from backend.models.email import Email
    return [Email(
        id=e.id,
        subject=e.subject,
        from_email=e.from_email,
        category_id=e.category_id,
        summary=e.summary,
        raw=e.raw,
        user_email=e.user_email,
        gmail_id=e.gmail_id,
        headers=e.headers if isinstance(e.headers, dict) else (json.loads(e.headers) if e.headers else None)  # Handle both dict and JSON string
    ) for e in db_emails]

def get_emails_by_user_email(user_email: str):
    """Get all emails for a specific user email, regardless of session"""
    db = SessionLocal()
    db_emails = db.query(DBEmail).filter(DBEmail.user_email == user_email).all()
    db.close()
    from backend.models.email import Email
    return [Email(
        id=e.id,
        subject=e.subject,
        from_email=e.from_email,
        category_id=e.category_id,
        summary=e.summary,
        raw=e.raw,
        user_email=e.user_email,
        gmail_id=e.gmail_id,
        headers=e.headers if isinstance(e.headers, dict) else (json.loads(e.headers) if e.headers else None)
    ) for e in db_emails]

def email_exists(user_email: str, gmail_id: str) -> bool:
    db = SessionLocal()
    exists = db.query(DBEmail).filter(DBEmail.user_email == user_email, DBEmail.gmail_id == gmail_id).first() is not None
    print(f"[EMAIL_EXISTS] Checking {user_email} with gmail_id {gmail_id}: {exists}")
    db.close()
    return exists

def create_session(session_id, primary_account, accounts):
    db = SessionLocal()
    db_session = DBSession(id=session_id, primary_account=primary_account)
    db.add(db_session)
    db.commit()
    for acc in accounts:
        db_account = DBSessionAccount(
            session_id=session_id,
            email=acc['email'],
            access_token=acc['access_token'],
            refresh_token=acc.get('refresh_token'),
            history_id=acc.get('history_id')
        )
        db.add(db_account)
    db.commit()
    db.close()
    return session_id

def add_account_to_session(session_id, email, access_token, refresh_token=None, history_id=None):
    db = SessionLocal()
    db_account = db.query(DBSessionAccount).filter_by(session_id=session_id, email=email).first()
    if db_account:
        db_account.access_token = access_token
        db_account.refresh_token = refresh_token
        db_account.history_id = history_id
    else:
        db_account = DBSessionAccount(
            session_id=session_id,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            history_id=history_id
        )
        db.add(db_account)
    db.commit()
    db.close()
    return True

def get_session(session_id):
    db = SessionLocal()
    session = db.query(DBSession).options(joinedload(DBSession.accounts)).filter_by(id=session_id).first()
    db.close()
    return session

def get_session_accounts(session_id):
    db = SessionLocal()
    accounts = db.query(DBSessionAccount).filter_by(session_id=session_id).all()
    db.close()
    return accounts

def set_primary_account(session_id, email):
    db = SessionLocal()
    session = db.query(DBSession).filter_by(id=session_id).first()
    if session:
        session.primary_account = email
        db.commit()
        db.close()
        return True
    db.close()
    return False

def get_primary_account(session_id):
    db = SessionLocal()
    session = db.query(DBSession).filter_by(id=session_id).first()
    db.close()
    return session.primary_account if session else None

def update_account_tokens(session_id, email, access_token, refresh_token=None, history_id=None):
    db = SessionLocal()
    acc = db.query(DBSessionAccount).filter_by(session_id=session_id, email=email).first()
    if acc:
        acc.access_token = access_token
        acc.refresh_token = refresh_token
        acc.history_id = history_id
        db.commit()
    db.close()
    return True

def get_account(session_id, email):
    db = SessionLocal()
    acc = db.query(DBSessionAccount).filter_by(session_id=session_id, email=email).first()
    db.close()
    return acc

# --- New utility functions for lookup by email ---
def get_account_by_email(email):
    db = SessionLocal()
    acc = db.query(DBSessionAccount).filter_by(email=email).first()
    db.close()
    return acc

def set_history_id_by_email(email, history_id):
    db = SessionLocal()
    acc = db.query(DBSessionAccount).filter_by(email=email).first()
    if acc:
        acc.history_id = history_id
        db.commit()
    db.close()
    return True

def get_history_id_by_email(email):
    db = SessionLocal()
    acc = db.query(DBSessionAccount).filter_by(email=email).first()
    db.close()
    return acc.history_id if acc else None

def find_session_id_by_email(email):
    db = SessionLocal()
    acc = db.query(DBSessionAccount).filter_by(email=email).first()
    db.close()
    return acc.session_id if acc else None

def get_or_create_session_by_email(email, access_token, refresh_token=None, history_id=None, force_new=False):
    """Get existing session for email or create new one. Returns session_id. If force_new, always create a new session."""
    db = SessionLocal()
    from backend.database.models import Session as DBSession, SessionAccount as DBSessionAccount
    import uuid
    if not force_new:
        acc = db.query(DBSessionAccount).filter_by(email=email).first()
        if acc:
            session_id = acc.session_id
            # Update tokens if needed
            acc.access_token = access_token
            acc.refresh_token = refresh_token
            acc.history_id = history_id
            db.commit()
            db.close()
            return session_id
    # Create new session
    session_id = str(uuid.uuid4())
    session = DBSession(id=session_id, primary_account=email)
    db.add(session)
    db.commit()
    db_account = DBSessionAccount(
        session_id=session_id,
        email=email,
        access_token=access_token,
        refresh_token=refresh_token,
        history_id=history_id
    )
    db.add(db_account)
    db.commit()
    db.close()
    return session_id

def remove_account_from_session(session_id, email):
    """Remove an account from a session. Returns True if successful, False if account not found."""
    db = SessionLocal()
    
    # Check if this is the last account in the session
    account_count = db.query(DBSessionAccount).filter_by(session_id=session_id).count()
    if account_count <= 1:
        db.close()
        return False, "Cannot remove the last account from a session"
    
    # Find and remove the account
    account = db.query(DBSessionAccount).filter_by(session_id=session_id, email=email).first()
    if not account:
        db.close()
        return False, "Account not found in session"
    
    # If this was the primary account, set a new primary account
    session = db.query(DBSession).filter_by(id=session_id).first()
    if session and session.primary_account == email:
        # Find another account to set as primary
        other_account = db.query(DBSessionAccount).filter_by(session_id=session_id).filter(DBSessionAccount.email != email).first()
        if other_account:
            session.primary_account = other_account.email
    
    # Remove the account
    db.delete(account)
    db.commit()
    db.close()
    
    return True, "Account removed successfully"

def get_or_create_uncategorized_category(user_email: str, session_id: str):
    """Get existing "Uncategorized" category for session or create new one. Returns the category."""
    db = SessionLocal()
    
    # First, try to find an existing "Uncategorized" category for this session
    from backend.database.models import Category as DBCategory
    
    # Look for an "Uncategorized" category in this session
    existing_uncategorized = db.query(DBCategory).filter(
        DBCategory.session_id == session_id,
        DBCategory.name == "Uncategorized"
    ).first()
    
    if existing_uncategorized:
        # Found existing "Uncategorized" category in this session
        print(f"[UNCATEGORIZED] Found existing category for session {session_id}: {existing_uncategorized.id}")
        
        # Get the values before closing the session
        category_id = existing_uncategorized.id
        category_name = existing_uncategorized.name
        category_description = existing_uncategorized.description
        db.close()
        
        # Migrate any orphaned emails to this category
        migrate_orphaned_emails_to_uncategorized(session_id)
        
        from backend.models.category import Category
        return Category(
            id=category_id,
            name=category_name,
            description=category_description,
            session_id=session_id
        )
    
    # No existing "Uncategorized" category found in this session, create a new one
    import uuid
    uncategorized_category = DBCategory(
        id=uuid.uuid4(),
        name="Uncategorized",
        description="Emails that don't fit other categories",
        session_id=session_id
    )
    db.add(uncategorized_category)
    db.commit()
    
    print(f"[UNCATEGORIZED] Created new category for session {session_id}: {uncategorized_category.id}")
    
    # Get the values before closing the session
    category_id = uncategorized_category.id
    category_name = uncategorized_category.name
    category_description = uncategorized_category.description
    db.close()
    
    # Migrate any orphaned emails to this new category
    migrate_orphaned_emails_to_uncategorized(session_id)
    
    from backend.models.category import Category
    return Category(
        id=category_id,
        name=category_name,
        description=category_description,
        session_id=session_id
    )

def migrate_orphaned_emails_to_uncategorized(session_id: str):
    """Migrate emails with invalid category_ids to the session's Uncategorized category"""
    db = SessionLocal()
    try:
        from backend.database.models import Category as DBCategory, Email as DBEmail
        
        # Get the Uncategorized category for this session
        uncategorized_category = db.query(DBCategory).filter(
            DBCategory.session_id == session_id,
            DBCategory.name == "Uncategorized"
        ).first()
        
        if not uncategorized_category:
            print(f"[MIGRATION] No Uncategorized category found for session {session_id}")
            return
        
        # Get all valid category IDs for this session
        valid_category_ids = {str(cat.id) for cat in db.query(DBCategory).filter(DBCategory.session_id == session_id).all()}
        
        # Find emails that have category_ids that don't exist in this session
        orphaned_emails = db.query(DBEmail).filter(
            DBEmail.category_id.notin_(valid_category_ids)
        ).all()
        
        if orphaned_emails:
            print(f"[MIGRATION] Found {len(orphaned_emails)} orphaned emails to migrate")
            for email in orphaned_emails:
                email.category_id = uncategorized_category.id
                print(f"[MIGRATION] Migrated email {email.id} to Uncategorized category")
            
            db.commit()
            print(f"[MIGRATION] Successfully migrated {len(orphaned_emails)} emails")
        else:
            print(f"[MIGRATION] No orphaned emails found")
            
    except Exception as e:
        print(f"[MIGRATION] Error migrating orphaned emails: {e}")
        db.rollback()
    finally:
        db.close()

def delete_session(session_id):
    """Delete a session and its associated data (accounts, categories) but preserve emails"""
    db = SessionLocal()
    try:
        # Get the session and its accounts
        session = db.query(DBSession).filter_by(id=session_id).first()
        if not session:
            return False
        
        # Get all accounts in this session
        accounts = db.query(DBSessionAccount).filter_by(session_id=session_id).all()
        account_emails = [acc.email for acc in accounts]
        
        # Delete categories for this session (emails will become orphaned but that's okay)
        from backend.database.models import Category as DBCategory
        categories = db.query(DBCategory).filter_by(session_id=session_id).all()
        for category in categories:
            db.delete(category)
        
        # Delete the session (this will cascade to accounts due to foreign key)
        db.delete(session)
        db.commit()
        
        print(f"Deleted session {session_id} with accounts: {account_emails}")
        print(f"Emails for these accounts are preserved in the database")
        return True
    except Exception as e:
        print(f"Error deleting session {session_id}: {e}")
        db.rollback()
        return False
    finally:
        db.close() 