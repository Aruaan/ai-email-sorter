import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
import os
from fastapi import Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from services.fake_db import get_user_token, get_categories_by_user
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

app.include_router(auth_router, prefix="/auth")
app.include_router(categories_router, prefix="/categories")

from fastapi.routing import APIRoute

for route in app.routes:
    if isinstance(route, APIRoute):
        print("ROUTE LOADED:", route.path)

@app.get("/dev/process-emails")
def dev_process_emails(user_email: str = Query(...), max_emails: int = Query(2)):
    """
    WARNING: This endpoint will call OpenAI for every email processed.
    Limit max_emails to avoid high costs!
    """
    user_token = get_user_token(user_email)
    categories = get_categories_by_user(user_email)
    return process_user_emails(user_token, categories, max_emails=max_emails)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)), reload=True)