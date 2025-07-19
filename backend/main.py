import uvicorn
from fastapi import FastAPI, Query
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware
from services.fake_db import get_user_token, get_categories_by_user, get_primary_account, get_session_accounts, create_user_session, add_account_to_session
from services.gmail_processor import process_user_emails

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
        
        categories = get_categories_by_user(user_token.email)
        if not categories:
            print(f"No categories found for user: {user_token.email}")
            return {"error": "No categories found. Please create categories first."}
        
        print(f"Found {len(categories)} categories for user: {user_token.email}")
        
        # Always use real Gmail API since user has proper OAuth tokens
        result = process_user_emails(user_token, categories, max_emails=max_emails)
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

@app.post("/dev/test/create-session")
def create_test_session(email: str = Query(...), access_token: str = Query("test-token"), refresh_token: str = Query("test-refresh")):
    """Create a test session for manual testing"""
    session_id = create_user_session(email, access_token, refresh_token)
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

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)