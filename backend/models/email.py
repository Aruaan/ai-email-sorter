from pydantic import BaseModel
from typing import Optional, Dict

class Email(BaseModel):
    id: int
    subject: str
    from_email: str
    category_id: int
    summary: str
    raw: str
    user_email: str
    gmail_id: str  # Gmail message ID
    headers: Optional[Dict[str, str]] = None