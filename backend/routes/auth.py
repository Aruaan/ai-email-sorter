from fastapi import APIRouter, Request, Response, status, Query
from fastapi.responses import RedirectResponse
from utils.google_oauth import get_auth_url, fetch_token, get_user_email
from services.fake_db import create_user_session, add_account_to_session, get_user_session, get_session_accounts, set_primary_account
from models.user import UserToken
import os

router = APIRouter()

@router.get("/google")
def google_login():
    url = get_auth_url()
    return RedirectResponse(url)

@router.get("/google/add-account")
def google_add_account(session_id: str = Query(...)):
    """Add another Gmail account to existing session"""
    url = get_auth_url(state=f"add_account:{session_id}")
    return RedirectResponse(url)

@router.get("/callback")
def google_callback(request: Request, code: str = "", state: str = ""):
    if not code:
        return Response(content="Missing code", status_code=status.HTTP_400_BAD_REQUEST)
    
    try:
        credentials = fetch_token(state, code)
        email = get_user_email(credentials)
    except Exception as e:
        return Response(content=f"Authentication failed: {str(e)}", status_code=status.HTTP_400_BAD_REQUEST)
    
    access_token = credentials.token if credentials.token is not None else ""
    refresh_token = credentials.refresh_token if credentials.refresh_token is not None else ""
    
    # Check if this is adding an account to existing session
    if state and state.startswith("add_account:"):
        session_id = state.split(":", 1)[1]
        success = add_account_to_session(session_id, email, access_token, refresh_token)
        if success:
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            redirect_url = f"{frontend_url}/dashboard?session_id={session_id}&account_added={email}"
            return RedirectResponse(url=redirect_url)
        else:
            return Response(content="Failed to add account to session", status_code=status.HTTP_400_BAD_REQUEST)
    
    # Create new session for first-time login
    session_id = create_user_session(email, access_token, refresh_token)
    
    # Redirect to frontend with session info
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_url = f"{frontend_url}/callback?session_id={session_id}&email={email}"
    return RedirectResponse(url=redirect_url)

@router.get("/session/{session_id}")
def get_session_info(session_id: str):
    """Get session information including all accounts"""
    session = get_user_session(session_id)
    if not session:
        return Response(content="Session not found", status_code=status.HTTP_404_NOT_FOUND)
    
    return {
        "session_id": session.session_id,
        "accounts": [{"email": acc.email} for acc in session.accounts],
        "primary_account": session.primary_account
    }

@router.post("/session/{session_id}/primary")
def set_primary_account_endpoint(session_id: str, email: str = Query(...)):
    """Set the primary account for a session"""
    success = set_primary_account(session_id, email)
    if not success:
        return Response(content="Account not found in session", status_code=status.HTTP_404_NOT_FOUND)
    
    return {"message": f"Primary account set to {email}"} 