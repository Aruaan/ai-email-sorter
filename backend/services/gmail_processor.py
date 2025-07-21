from typing import List, Dict, Any
from models.user import UserToken
from models.category import Category
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import openai
import os
import base64
from dotenv import load_dotenv
from services.session_db import save_email, email_exists
from models.email import Email

load_dotenv()
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
print(f"Using OpenAI model: {OPENAI_MODEL}")

def summarize_email(subject: str, sender: str, recipient: str, text: str, categories: list) -> str:
    category_descriptions = "\n".join([f"{c.name}: {c.description}" for c in categories])
    prompt = f"""
You're an AI assistant. Summarize the email below in 1-2 sentences. Focus on what it's about. Be concise and clear.

Email:
Subject: {subject}
From: {sender}
To: {recipient}
Body:
{text}

Respond only with the summary. Don't include any labels, categories, or extra commentary.
"""
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=100
        )
        content = response.choices[0].message.content.strip()
        return content
    except Exception as e:
        print(f"[Summary error]: {e}")
        return "Summary not available."

def classify_email(text: str, categories: List[Category]) -> int:
    category_descriptions = "\n".join([f"{c.name}: {c.description}" for c in categories])
    prompt = f"""
Given the following email content:
---
{text}
---

And these categories:
{category_descriptions}

Which category does the email best belong to? Only return the category name.
"""
    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=50
        )
        name = response.choices[0].message.content.strip().lower()
        for cat in categories:
            if cat.name.lower() in name:
                return cat.id
    except Exception as e:
        print(f"[Classification error]: {e}")

    # Fallback: find 'Uncategorized' or use the first category
    fallback = next((c for c in categories if c.name.lower() == "uncategorized"), categories[0])
    return fallback.id

def archive_gmail_message(service, gmail_id):
    try:
        service.users().messages().modify(
            userId='me',
            id=gmail_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        print(f"Archived Gmail message {gmail_id}")
    except Exception as e:
        if 'not found' in str(e).lower():
            print(f"Gmail message {gmail_id} already gone.")
        else:
            print(f"Archive failed for {gmail_id}: {e}")

def get_latest_history_id(service) -> str:
    profile = service.users().getProfile(userId='me').execute()
    return profile.get('historyId')

def get_new_message_ids(service, last_history_id: str) -> list:
    new_message_ids = set()
    page_token = None
    while True:
        history = service.users().history().list(
            userId='me',
            startHistoryId=last_history_id,
            historyTypes=['messageAdded'],
            pageToken=page_token
        ).execute()
        for h in history.get('history', []):
            for msg in h.get('messagesAdded', []):
                new_message_ids.add(msg['message']['id'])
        page_token = history.get('nextPageToken')
        if not page_token:
            break
    return list(new_message_ids)

def process_user_emails(user_token: UserToken, categories: List[Category], max_emails: int = 10, last_history_id: str = "") -> List[dict]:
    try:
        print(f"Processing emails for user: {user_token.email}")
        creds = Credentials(
            token=user_token.access_token,
            refresh_token=user_token.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=None,
            client_secret=None
        )
        service = build('gmail', 'v1', credentials=creds)

        if not categories:
            print(f"No categories available for user {user_token.email}")
            return []

        if not last_history_id:
            from services.session_db import set_history_id_by_email
            current_history_id = get_latest_history_id(service)
            set_history_id_by_email(user_token.email, current_history_id)
            print(f"Set initial history ID for {user_token.email} to {current_history_id}")
            return []

        new_message_ids = get_new_message_ids(service, last_history_id)
        print(f"Found {len(new_message_ids)} new messages.")

        processed = []
        for gmail_id in new_message_ids[:max_emails]:
            try:
                if email_exists(user_token.email, gmail_id):
                    print(f"Skipping already-processed message: {gmail_id}")
                    continue

                msg_detail = service.users().messages().get(userId='me', id=gmail_id, format='full').execute()
                label_ids = msg_detail.get('labelIds', [])
                if 'INBOX' not in label_ids or 'SENT' in label_ids or 'DRAFT' in label_ids:
                    print(f"Skipping non-inbox message: {gmail_id}")
                    continue

                headers = {h['name']: h['value'] for h in msg_detail['payload'].get('headers', [])}
                subject = headers.get('Subject', '')
                sender = headers.get('From', '')
                recipient = headers.get('To', '') or headers.get('Delivered-To', '')
                snippet = msg_detail.get('snippet', '')
                body = ''
                for part in msg_detail['payload'].get('parts', []):
                    if part.get('mimeType') == 'text/plain':
                        data = part['body'].get('data')
                        if data:
                            body = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                            break
                if not body:
                    body = snippet

                category_id = classify_email(body, categories)
                summary = summarize_email(subject, sender, recipient, body, categories)

                email_obj = Email(
                    id=None,  # Let the database generate the UUID
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
                archive_gmail_message(service, gmail_id)
                processed.append(email_obj.model_dump())
            except Exception as e:
                print(f"[Processing error for {gmail_id}]: {e}")
                continue

        return processed

    except Exception as e:
        print(f"[Critical error in process_user_emails]: {e}")
        raise e
