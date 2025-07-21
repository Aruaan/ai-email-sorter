from dotenv import load_dotenv
from httpx import request
import uvicorn
from fastapi import FastAPI, Query, Request, Header, Body
import os
from fastapi.middleware.cors import CORSMiddleware
from services.session_db import get_session, get_session_accounts, get_primary_account, set_primary_account, get_account, get_account_by_email, get_history_id_by_email, set_history_id_by_email, find_session_id_by_email
from services.gmail_processor import process_user_emails
import logging
from database.db import engine, Base

# Load environment variables from .env
load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
Base.metadata.create_all(bind=engine)
# Import and include routers
from routes.auth import router as auth_router
from routes.categories import router as categories_router
from routes.emails import router as emails_router

app.include_router(auth_router, prefix="/auth")
app.include_router(categories_router, prefix="/categories")
app.include_router(emails_router, prefix="/emails")

from fastapi.routing import APIRoute

for route in app.routes:
    if isinstance(route, APIRoute):
        print("ROUTE LOADED:", route.path)

# Track emails we've already logged 'no user token found' for
no_token_logged_emails = set()

@app.get("/dev/process-emails")
def dev_process_emails(session_id: str = Query(...), email: str = Query(None), max_emails: int = Query(3), force: bool = Query(False)):
    try:
        print(f"Processing emails request - session_id: {session_id}, email: {email}, max_emails: {max_emails}")
        
        if email:
            acc = get_account(session_id, email)
        else:
            primary_email = get_primary_account(session_id)
            acc = get_account(session_id, primary_email)
        if not acc:
            print(f"User token not found for session {session_id}")
            return {"error": "User token not found"}
        print(f"Found user token for: {acc.email}")
        from services.session_db import get_categories_by_session
        categories = get_categories_by_session(session_id)
        if not categories:
            # Get or create "Uncategorized" category for this user
            print(f"No categories found for session: {session_id}, getting or creating 'Uncategorized' category")
            from services.session_db import get_or_create_uncategorized_category
            
            # Get the primary account email for this session
            primary_email = get_primary_account(session_id)
            if primary_email:
                uncategorized_category = get_or_create_uncategorized_category(primary_email, session_id)
                categories = [uncategorized_category]
                print(f"Got or created 'Uncategorized' category for user {primary_email}")
            else:
                print(f"No primary account found for session {session_id}")
                return {"error": "No primary account found"}
        print(f"Found {len(categories)} categories for session: {session_id}")
        # Always use real Gmail API since user has proper OAuth tokens
        # Build a UserToken-like object for process_user_emails
        from models.user import UserToken
        user_token = UserToken(
            email=acc.email,
            access_token=acc.access_token,
            refresh_token=acc.refresh_token,
            history_id=acc.history_id
        )
        # If force=True, use empty history_id to process all recent emails
        history_id_to_use = "" if force else ""
        result = process_user_emails(user_token, categories, max_emails=max_emails, last_history_id=history_id_to_use)
        print(f"Email processing result: {type(result)}, length: {len(result) if isinstance(result, list) else 'N/A'}")
        return result
        
    except Exception as e:
        print(f"Error in dev_process_emails: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Failed to process emails: {str(e)}"}

@app.get("/dev/session/{session_id}/accounts")
def get_session_accounts_endpoint(session_id: str):
    """Get all accounts in a session"""
    accounts = get_session_accounts(session_id)
    return {
        "session_id": session_id,
        "accounts": [{"email": acc.email} for acc in accounts]
    }

@app.get("/dev/process-all-accounts")
def process_all_accounts(session_id: str = Query(...), max_emails: int = Query(3)):
    """Process emails for all accounts in a session"""
    accounts = get_session_accounts(session_id)
    if not accounts:
        return {"error": "No accounts found for session"}
    
    results = {}
    for acc in accounts:
        try:
            # Get categories for this session
            from services.session_db import get_categories_by_session
            categories = get_categories_by_session(session_id)
            if not categories:
                # Get or create "Uncategorized" category
                from services.session_db import get_or_create_uncategorized_category
                primary_email = get_primary_account(session_id)
                if primary_email:
                    uncategorized_category = get_or_create_uncategorized_category(primary_email, session_id)
                    categories = [uncategorized_category]
            
            # Build UserToken
            from models.user import UserToken
            user_token = UserToken(
                email=acc.email,
                access_token=acc.access_token,
                refresh_token=acc.refresh_token,
                history_id=acc.history_id
            )
            
            # Process emails for this account
            result = process_user_emails(user_token, categories, max_emails=max_emails, last_history_id="")
            results[acc.email] = {
                "processed": len(result),
                "emails": result
            }
        except Exception as e:
            results[acc.email] = {"error": str(e)}
    
    return {"session_id": session_id, "results": results}

# On session creation/login, log the email and session ID
@app.post("/dev/test/create-session")
def create_test_session(email: str = Query(...), access_token: str = Query("test-token"), refresh_token: str = Query("test-refresh")):
    """Create a test session for manual testing"""
    import uuid
    session_id = str(uuid.uuid4())
    from services.session_db import create_session
    create_session(session_id, email, [{
        "email": email,
        "access_token": access_token,
        "refresh_token": refresh_token
    }])
    print(f"[SESSION CREATED] Email: {email}, Session ID: {session_id}")
    return {
        "session_id": session_id,
        "email": email,
        "message": "Test session created"
    }

@app.post("/dev/test/add-account")
def add_test_account(session_id: str = Query(...), email: str = Query(...), access_token: str = Query("test-token"), refresh_token: str = Query("test-refresh")):
    """Add a test account to an existing session"""
    from services.session_db import add_account_to_session
    add_account_to_session(session_id, email, access_token, refresh_token)
    return {
        "session_id": session_id,
        "email": email,
        "message": "Account added to session"
    }

@app.post("/webhook/test")
async def test_webhook(request: Request):
    data = await request.json()
    print("Webhook received data:", data)
    return {"status": "ok", "received": data}

@app.post("/gmail/webhook")
async def gmail_webhook(request: Request, authorization: str = Header(None)):
    body = await request.json()
    print("== RAW PubSub BODY ==\n", body)

    # If payload unwrapping is enabled, emailAddress/historyId are at the top level
    email_address = body.get("emailAddress")
    history_id = body.get("historyId")

    if not email_address or not history_id:
        logging.warning("Missing emailAddress or historyId in body")
        return {"status": "missing attributes"}

    logging.info(f"[GMAIL WEBHOOK] email: {email_address}, historyId: {history_id}")

    # Find the session and account for this email
    session_id = find_session_id_by_email(email_address)
    if not session_id:
        if email_address not in no_token_logged_emails:
            logging.warning(f"No session found for {email_address}")
            no_token_logged_emails.add(email_address)
        return {"status": "user not found"}
    
    # Get the account details
    acc = get_account(session_id, email_address)
    if not acc:
        logging.warning(f"No account found for {email_address} in session {session_id}")
        return {"status": "account not found"}
    
    # Get categories for this session
    from services.session_db import get_categories_by_session
    categories = get_categories_by_session(session_id)
    print(f"[WEBHOOK] Found {len(categories)} categories for session {session_id}: {[c.name for c in categories]}")
    
    if not categories:
        # Get or create "Uncategorized" category for this user
        logging.info(f"No categories found for session {session_id}, getting or creating 'Uncategorized' category")
        from services.session_db import get_or_create_uncategorized_category
        
        # Get the primary account email for this session
        primary_email = get_primary_account(session_id)
        if primary_email:
            uncategorized_category = get_or_create_uncategorized_category(primary_email, session_id)
            categories = [uncategorized_category]
            logging.info(f"Got or created 'Uncategorized' category for user {primary_email}")
            print(f"[WEBHOOK] Created 'Uncategorized' category: {uncategorized_category.name} (ID: {uncategorized_category.id})")
        else:
            logging.error(f"No primary account found for session {session_id}")
            return {"status": "no primary account"}

    # Get last processed historyId
    last_history_id = get_history_id_by_email(email_address)
    print(f"[GMAIL WEBHOOK] Last processed historyId for {email_address}: {last_history_id}")
    logging.info(f"[GMAIL WEBHOOK] Last processed historyId for {email_address}: {last_history_id}")
    
    # Debug: Check if this history_id is newer than what we have
    if last_history_id:
        try:
            last_history_int = int(last_history_id)
            if history_id <= last_history_int:
                print(f"[GMAIL WEBHOOK] Skipping - history_id {history_id} is not newer than last processed {last_history_id}")
                return {"status": "already processed"}
        except (ValueError, TypeError):
            print(f"[GMAIL WEBHOOK] Warning: Could not parse last_history_id '{last_history_id}' as integer")

    # Call process_user_emails with last_history_id
    try:
        from models.user import UserToken
        user_token = UserToken(
            email=acc.email,
            access_token=acc.access_token,
            refresh_token=acc.refresh_token,
            history_id=acc.history_id
        )
        processed = process_user_emails(user_token, categories, last_history_id=last_history_id or "")
        print(f"[GMAIL WEBHOOK] Processed {len(processed)} emails for {email_address}")
        logging.info(f"[GMAIL WEBHOOK] Processed {len(processed)} emails for {email_address}")
        # Update stored historyId to the latest from Gmail
        from services.gmail_processor import get_latest_history_id
        creds = acc.access_token
        refresh = acc.refresh_token
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        creds_obj = Credentials(token=creds, refresh_token=refresh, token_uri="https://oauth2.googleapis.com/token", client_id=None, client_secret=None)
        service = build('gmail', 'v1', credentials=creds_obj)
        latest_history_id = get_latest_history_id(service)
        set_history_id_by_email(email_address, latest_history_id)
        print(f"[GMAIL WEBHOOK] Updated historyId for {email_address} to {latest_history_id}")
        logging.info(f"[GMAIL WEBHOOK] Updated historyId for {email_address} to {latest_history_id}")
    except Exception as e:
        logging.error(f"Error processing emails for {email_address}: {e}")
        return {"status": "processing error"}

    return {"status": "ok", "processed": len(processed), "history_id": latest_history_id}

@app.post("/dev/migrate-orphaned-emails")
def migrate_orphaned_emails_endpoint(session_id: str = Query(...)):
    """Manually migrate orphaned emails to the session's Uncategorized category"""
    from services.session_db import migrate_orphaned_emails_to_uncategorized
    migrate_orphaned_emails_to_uncategorized(session_id)
    return {"message": "Migration completed"}

@app.get("/dev/debug/sessions")
def debug_sessions_endpoint():
    """Debug endpoint to see all sessions and their categories"""
    from services.session_db import get_session
    from database.models import Session as DBSession, Category as DBCategory
    from database.db import SessionLocal
    
    db = SessionLocal()
    try:
        sessions = db.query(DBSession).all()
        result = []
        
        for session in sessions:
            categories = db.query(DBCategory).filter(DBCategory.session_id == session.id).all()
            result.append({
                "session_id": session.id,
                "primary_account": session.primary_account,
                "categories": [{"id": str(cat.id), "name": cat.name, "description": cat.description} for cat in categories]
            })
        
        return {"sessions": result}
    finally:
        db.close()

@app.post("/dev/gmail-watch")
def dev_gmail_watch(user_email: str = Body(...)):
    """Register Gmail watch for the given user (for debugging Google Pub/Sub webhook setup)."""
    # Find the session for this email
    session_id = find_session_id_by_email(user_email)
    if not session_id:
        return {"error": f"No session found for {user_email}"}
    
    # Get the account details
    acc = get_account(session_id, user_email)
    if not acc:
        return {"error": f"No account found for {user_email}"}
    
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(
        token=acc.access_token,
        refresh_token=acc.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,
        client_secret=None
    )
    service = build('gmail', 'v1', credentials=creds)
    topic_name = os.getenv("GMAIL_PUBSUB_TOPIC")
    webhook_url = os.getenv("GMAIL_WEBHOOK_URL")
    if not topic_name or not webhook_url:
        return {"error": "Missing GMAIL_PUBSUB_TOPIC or GMAIL_WEBHOOK_URL in .env. Set these to your Google Cloud Pub/Sub topic and webhook URL."}
    try:
        request_body = {
            "topicName": topic_name,
            "labelIds": ["INBOX"],
            "labelFilterAction": "include"
        }
        resp = service.users().watch(userId='me', body=request_body).execute()
        history_id = resp.get("historyId")
        if history_id:
            set_history_id_by_email(user_email, history_id)
        logging.info(f"Gmail watch response: {resp}")
        return {"status": "watch registered", "response": resp}
    except Exception as e:
        logging.error(f"Failed to register Gmail watch: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)