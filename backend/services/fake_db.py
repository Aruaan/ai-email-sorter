from typing import Dict, List
from models.category import Category
from models.user import UserToken
from models.email import Email

# In-memory stores
users: Dict[str, UserToken] = {}
categories: List[Category] = []
emails: List[Email] = []
_email_id_counter = 1

# User token management
def save_user_token(user_token: UserToken):
    users[user_token.email] = user_token

def get_user_token(email: str) -> UserToken:
    user = users.get(email)
    if user is None:
        raise ValueError(f"User with email {email} not found")
    return user

# Category management
def add_category(category: Category):
    categories.append(category)

def get_categories_by_user(email: str) -> List[Category]:
    return [cat for cat in categories if cat.user_email == email]

def save_email(email: Email):
    global _email_id_counter
    email.id = _email_id_counter
    _email_id_counter += 1
    emails.append(email)

def get_emails_by_user_and_category(user_email: str, category_id: int) -> List[Email]:
    return [e for e in emails if e.user_email == user_email and e.category_id == category_id]

def email_exists(user_email: str, gmail_id: str) -> bool:
    return any(e for e in emails if e.user_email == user_email and e.gmail_id == gmail_id) 