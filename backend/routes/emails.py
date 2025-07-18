from fastapi import APIRouter, Query
from typing import List
from models.email import Email
from services.fake_db import get_emails_by_user_and_category

router = APIRouter()

@router.get("/", response_model=List[Email])
def list_emails(user_email: str = Query(...), category_id: int = Query(...)):
    return get_emails_by_user_and_category(user_email, category_id) 