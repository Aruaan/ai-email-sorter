from typing import List, Dict, Any
from models.user import UserToken
from models.category import Category
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import openai
import os
from dotenv import load_dotenv
load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use a cheaper model for dev/testing
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
print(f"Using OpenAI model: {OPENAI_MODEL}")

from services.fake_db import save_email, email_exists
from models.email import Email

def summarize_email(text: str) -> str:
    prompt = f"Summarize the following email in 1-2 sentences:\n\n{text}"
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5,
        max_tokens=100
    )
    content = response.choices[0].message.content if response.choices[0].message and response.choices[0].message.content else ""
    return content.strip()

def classify_email(text: str, categories: List[Category]) -> int:
    category_descriptions = "\n".join(
        [f"{c.name}: {c.description}" for c in categories]
    )
    prompt = f"""
Given the following email content:
---
{text}
---

And these categories:
{category_descriptions}

Which category does the email best belong to? Only return the category name.
"""
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=50
    )
    name = response.choices[0].message.content if response.choices[0].message and response.choices[0].message.content else ""
    name = name.strip()
    for cat in categories:
        if cat.name.lower() in name.lower():
            return cat.id
    return -1  # fallback


def archive_gmail_message(service, gmail_id):
    try:
        service.users().messages().modify(
            userId='me',
            id=gmail_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
    except Exception as e:
        print(f"Failed to archive Gmail message {gmail_id}: {e}")


def process_user_emails(user_token: UserToken, categories: List[Category], max_emails: int = 2) -> List[Dict[str, Any]]:
    creds = Credentials(
        token=user_token.access_token,
        refresh_token=user_token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=None,
        client_secret=None
    )
    service = build('gmail', 'v1', credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=max_emails).execute()
    messages = results.get('messages', [])[:max_emails]
    processed = []
    for msg in messages:
        gmail_id = msg['id']
        if email_exists(user_token.email, gmail_id):
            continue  # Skip already processed
        msg_detail = service.users().messages().get(userId='me', id=gmail_id, format='full').execute()
        headers = {h['name']: h['value'] for h in msg_detail['payload'].get('headers', [])}
        subject = headers.get('Subject', '')
        sender = headers.get('From', '')
        snippet = msg_detail.get('snippet', '')
        # Try to get plain text body
        body = ''
        parts = msg_detail['payload'].get('parts', [])
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                data = part['body'].get('data')
                if data:
                    import base64
                    body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                    break
        if not body:
            body = snippet
        category_id = classify_email(body, categories)
        summary = summarize_email(body)
        email_obj = Email(
            id=0,  # Will be set by save_email
            subject=subject,
            from_email=sender,
            category_id=category_id,
            summary=summary,
            raw=body,
            user_email=user_token.email,
            gmail_id=gmail_id,
            headers=headers
        )
        save_email(email_obj)
        # Archive the email in Gmail
        archive_gmail_message(service, gmail_id)
        processed.append(email_obj.model_dump())
    return processed 