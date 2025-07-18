from typing import Dict, List
from models.category import Category
from models.user import UserToken

# In-memory stores
users: Dict[str, UserToken] = {}
categories: List[Category] = []

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