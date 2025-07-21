from pydantic import BaseModel
from typing import Optional, Dict
import uuid

class Email(BaseModel):
    id: Optional[uuid.UUID] = None
    subject: str
    from_email: str
    category_id: uuid.UUID
    summary: str
    raw: str
    user_email: str
    gmail_id: str  # Gmail message ID
    headers: Optional[Dict[str, str]] = None