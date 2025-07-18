from fastapi import APIRouter, Query, Body
from typing import List
from models.email import Email
from services.fake_db import get_emails_by_user_and_category, emails
from utils.unsubscribe import extract_unsubscribe_links

router = APIRouter()

@router.get("/", response_model=List[Email])
def list_emails(user_email: str = Query(...), category_id: int = Query(...)):
    return get_emails_by_user_and_category(user_email, category_id)

@router.post("/unsubscribe")
def unsubscribe_from_emails(email_ids: list = Body(...)):
    results = []
    for eid in email_ids:
        email = next((e for e in emails if e.id == eid), None)
        if email:
            links = extract_unsubscribe_links(email)
            results.append({"email_id": eid, "unsubscribe_links": links})
        else:
            results.append({"email_id": eid, "unsubscribe_links": [], "error": "Email not found"})
    return results 