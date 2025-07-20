from fastapi import APIRouter, Query, Body
from typing import List
from models.email import Email
from services.fake_db import get_emails_by_user_and_category, emails, get_session_accounts
from utils.unsubscribe import extract_unsubscribe_links

router = APIRouter()

@router.get("/", response_model=List[Email])
def list_emails(session_id: str = Query(...), category_id: int = Query(...)):
    accounts = get_session_accounts(session_id)
    if not accounts:
        return []
    all_emails = []
    for account in accounts:
        all_emails.extend(get_emails_by_user_and_category(account.email, category_id))
    # Convert to Pydantic models
    return [Email(
        id=e.id,
        subject=e.subject,
        from_email=e.from_email,
        category_id=e.category_id,
        summary=e.summary,
        raw=e.raw,
        user_email=e.user_email,
        gmail_id=e.gmail_id,
        headers=getattr(e, 'headers', None)
    ) for e in all_emails]

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