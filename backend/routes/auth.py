from fastapi import APIRouter, Request, Response, status
from fastapi.responses import RedirectResponse
from utils.google_oauth import get_auth_url, fetch_token, get_user_email
from services.fake_db import save_user_token
from models.user import UserToken
import os

router = APIRouter()

@router.get("/google")
def google_login():
    url = get_auth_url()
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
    user_token = UserToken(
        email=email,
        access_token=access_token,
        refresh_token=refresh_token
    )
    save_user_token(user_token)
    print(f"Saved user token for: {email}")
    
    # Redirect to frontend with email
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_url = f"{frontend_url}/callback?email={email}"
    return RedirectResponse(url=redirect_url) 