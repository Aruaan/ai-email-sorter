from fastapi import APIRouter, Query, Body
from typing import List
from models.email import Email
from services.session_db import get_emails_by_user_and_category, email_exists, save_email
from services.session_db import get_session_accounts
from utils.unsubscribe import extract_unsubscribe_links
from services.unsubscribe_worker import batch_unsubscribe_worker
from email.parser import HeaderParser

router = APIRouter()

@router.get("/", response_model=List[Email])
def list_emails(session_id: str = Query(...), category_id: str = Query(...), user_email: str = Query(None)):
    print(f"[EMAILS API] Request: session_id={session_id}, category_id={category_id}, user_email={user_email}")
    
    accounts = get_session_accounts(session_id)
    print(f"[EMAILS API] Found {len(accounts)} accounts: {[acc.email for acc in accounts]}")
    
    if not accounts:
        print("[EMAILS API] No accounts found, returning empty list")
        return []
    
    all_emails = []
    
    # If user_email is specified, only get emails for that specific account
    if user_email:
        print(f"[EMAILS API] Filtering for specific user: {user_email}")
        # Verify the user_email belongs to this session
        account_emails = [acc.email for acc in accounts]
        if user_email in account_emails:
            # Get emails for this specific category
            category_emails = get_emails_by_user_and_category(user_email, category_id)
            print(f"[EMAILS API] Found {len(category_emails)} emails for {user_email} in category {category_id}")
            all_emails.extend(category_emails)
            
            # If this is the "Uncategorized" category, also include orphaned emails (emails with invalid category_ids)
            if category_id and "uncategorized" in category_id.lower():
                from services.session_db import get_emails_by_user_email, get_categories_by_session
                all_user_emails = get_emails_by_user_email(user_email)
                
                # Get all valid category IDs for this session
                session_categories = get_categories_by_session(session_id)
                valid_category_ids = {str(cat.id) for cat in session_categories}
                
                # Find emails that have category_ids that don't exist in this session (orphaned emails)
                orphaned_emails = []
                for email in all_user_emails:
                    if email.category_id:
                        # Check if this email's category_id exists in the current session
                        if str(email.category_id) not in valid_category_ids:
                            # This email has a category_id from an old session, treat it as orphaned
                            orphaned_emails.append(email)
                    else:
                        # Email has no category_id at all
                        orphaned_emails.append(email)
                
                print(f"[EMAILS API] Found {len(orphaned_emails)} orphaned emails for {user_email}")
                all_emails.extend(orphaned_emails)
        else:
            print(f"[EMAILS API] User {user_email} not found in session accounts")
    else:
        print(f"[EMAILS API] Getting emails for all accounts in session")
        # Get emails for all accounts in the session (existing behavior)
        for account in accounts:
            account_emails = get_emails_by_user_and_category(account.email, category_id)
            print(f"[EMAILS API] Found {len(account_emails)} emails for {account.email} in category {category_id}")
            all_emails.extend(account_emails)
    
    print(f"[EMAILS API] Returning {len(all_emails)} total emails")
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
    print("DEBUG: Received unsubscribe request for email_ids:", email_ids)
    results = []
    for eid in email_ids:
        from database.db import SessionLocal
        from database.models import Email as DBEmail
        import json
        db = SessionLocal()
        db_email = db.query(DBEmail).filter(DBEmail.id == eid).first()
        db.close()
        if db_email:
            # Parse headers from JSON string if needed
            if isinstance(db_email.headers, str):
                try:
                    headers = json.loads(db_email.headers)
                except json.JSONDecodeError:
                    # Fallback to header parser for old format
                    headers = dict(HeaderParser().parsestr(db_email.headers).items())
            else:
                headers = db_email.headers or {}
            
            # Normalize headers
            headers = {k.lower(): v for k, v in headers.items()}
            print("DEBUG: Email headers:", headers)
            print("DEBUG: Email raw (first 200 chars):", db_email.raw[:200])
            
            # Create Email object for unsubscribe processing
            from models.email import Email
            email_obj = Email(
                id=db_email.id,
                subject=db_email.subject,
                from_email=db_email.from_email,
                category_id=db_email.category_id,
                summary=db_email.summary,
                raw=db_email.raw,
                user_email=db_email.user_email,
                gmail_id=db_email.gmail_id,
                headers=headers
            )
            
            links = extract_unsubscribe_links(email_obj)
            print(f"DEBUG: Unsubscribe links found for email {eid}:", links)
            results.append({"email_id": eid, "unsubscribe_links": links})
        else:
            print(f"DEBUG: Email ID {eid} not found!")
            results.append({"email_id": eid, "unsubscribe_links": [], "error": "Email not found"})
    print("DEBUG: Final unsubscribe results:", results)
    return results

@router.post("/unsubscribe/ai")
def ai_unsubscribe_from_links(payload: dict = Body(...)):
    """AI-powered batch unsubscribe: expects {"unsubscribe_links": [...], "user_email": ...} in payload."""
    unsubscribe_links = payload.get("unsubscribe_links", [])
    user_email = payload.get("user_email")
    results = batch_unsubscribe_worker(unsubscribe_links, user_email)
    return {"results": results}

@router.delete("/")
def delete_emails(email_ids: list = Body(...)):
    """Delete multiple emails by their IDs"""
    from database.db import SessionLocal
    from database.models import Email as DBEmail
    
    db = SessionLocal()
    deleted_count = 0
    failed_ids = []
    
    try:
        for email_id in email_ids:
            email = db.query(DBEmail).filter(DBEmail.id == email_id).first()
            if email:
                db.delete(email)
                deleted_count += 1
            else:
                failed_ids.append(email_id)
        
        db.commit()
        return {
            "message": f"Successfully deleted {deleted_count} email(s)",
            "deleted_count": deleted_count,
            "failed_ids": failed_ids
        }
    except Exception as e:
        db.rollback()
        return {"error": f"Failed to delete emails: {str(e)}"}
    finally:
        db.close() 