from dotenv import load_dotenv
from httpx import request
import uvicorn
from fastapi import FastAPI, Query, Request, Header, Body
import os
from fastapi.middleware.cors import CORSMiddleware
from services.fake_db import get_user_token, get_categories_by_session, get_primary_account, get_session_accounts, create_user_session, add_account_to_session, get_user_token_by_email, get_history_id_by_email, set_history_id_by_email
from services.gmail_processor import process_user_emails
import logging
from database.db import engine, Base
from database.models import Category, Email


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
def dev_process_emails(session_id: str = Query(...), email: str = Query(None), max_emails: int = Query(3)):
    try:
        print(f"Processing emails request - session_id: {session_id}, email: {email}, max_emails: {max_emails}")
        
        if email:
            user_token = get_user_token(session_id, email)
        else:
            user_token = get_primary_account(session_id)
        
        if not user_token:
            print(f"User token not found for session {session_id}")
            return {"error": "User token not found"}
        
        print(f"Found user token for: {user_token.email}")
        
        categories = get_categories_by_session(session_id)
        if not categories:
            print(f"No categories found for session: {session_id}")
            return {"error": "No categories found. Please create categories first."}
        
        print(f"Found {len(categories)} categories for session: {session_id}")
        
        # Always use real Gmail API since user has proper OAuth tokens
        result = process_user_emails(user_token, categories, max_emails=max_emails, last_history_id="")
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

# On session creation/login, log the email and session ID
@app.post("/dev/test/create-session")
def create_test_session(email: str = Query(...), access_token: str = Query("test-token"), refresh_token: str = Query("test-refresh")):
    """Create a test session for manual testing"""
    session_id = create_user_session(email, access_token, refresh_token)
    print(f"[SESSION CREATED] Email: {email}, Session ID: {session_id}")
    return {
        "session_id": session_id,
        "email": email,
        "message": "Test session created"
    }

@app.post("/dev/test/add-account")
def add_test_account(session_id: str = Query(...), email: str = Query(...), access_token: str = Query("test-token"), refresh_token: str = Query("test-refresh")):
    """Add a test account to an existing session"""
    success = add_account_to_session(session_id, email, access_token, refresh_token)
    if success:
        return {
            "session_id": session_id,
            "email": email,
            "message": "Account added to session"
        }
    else:
        return {"error": "Failed to add account to session"}

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

    # Now continue with rest of your logic (unchanged)
    user_token = get_user_token_by_email(email_address)
    if not user_token:
        if email_address not in no_token_logged_emails:
            logging.warning(f"No user token found for {email_address}")
            no_token_logged_emails.add(email_address)
        return {"status": "user not found"}
    # Find the session for this user
    session_id = None
    for sid, session in get_session_accounts.__globals__["user_sessions"].items():
        if any(acc.email == email_address for acc in session.accounts):
            session_id = sid
            break
    if not session_id:
        logging.error(f"No session found for {email_address}")
        return {"status": "no session"}
    categories = get_categories_by_session(session_id)
    if not categories:
        logging.error(f"No categories found for session {session_id}")
        return {"status": "no categories"}

    # Get last processed historyId
    last_history_id = get_history_id_by_email(email_address)
    print(f"[GMAIL WEBHOOK] Last processed historyId for {email_address}: {last_history_id}")
    logging.info(f"[GMAIL WEBHOOK] Last processed historyId for {email_address}: {last_history_id}")

    # Call process_user_emails with last_history_id
    try:
        # Process emails using the stored history ID
        processed = process_user_emails(user_token, categories, last_history_id=last_history_id or "")

        
        print(f"[GMAIL WEBHOOK] Processed {len(processed)} emails for {email_address}")
        logging.info(f"[GMAIL WEBHOOK] Processed {len(processed)} emails for {email_address}")
        
        # Update stored historyId to the latest from Gmail
        from services.gmail_processor import get_latest_history_id
        creds = user_token.access_token
        refresh = user_token.refresh_token
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

@app.post("/dev/gmail-watch")
def dev_gmail_watch(user_email: str = Body(...)):
    """Register Gmail watch for the given user (for debugging Google Pub/Sub webhook setup)."""
    from services.fake_db import get_user_token_by_email
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    import os
    import logging
    # Get user token
    user_token = get_user_token_by_email(user_email)
    if not user_token:
        return {"error": f"No user token found for {user_email}"}
    creds = Credentials(
        token=user_token.access_token,
        refresh_token=user_token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,
        client_secret=None
    )
    service = build('gmail', 'v1', credentials=creds)
    # Get Pub/Sub topic and webhook URL from env
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