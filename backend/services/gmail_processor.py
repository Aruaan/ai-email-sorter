from typing import List, Dict, Any
from models.user import UserToken
from models.category import Category
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import openai
import os
import base64
from dotenv import load_dotenv
load_dotenv()

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use a cheaper model for dev/testing
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
print(f"Using OpenAI model: {OPENAI_MODEL}")

from services.fake_db import save_email, email_exists
from models.email import Email

def summarize_email(subject: str, sender: str, recipient: str, text: str, categories: list) -> str:
    category_descriptions = "\n".join([f"{c.name}: {c.description}" for c in categories])
    prompt = f"""
Summarize the following email in 1-2 sentences, focusing on what it's about and who it's for. Use the subject, sender, and recipient for context. Then, suggest which of these categories it best fits, based on their descriptions:

Subject: {subject}
From: {sender}
To: {recipient}

Email body:
{text}

Categories:
{category_descriptions}
"""
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
        resp = service.users().messages().modify(
            userId='me',
            id=gmail_id,
            body={'removeLabelIds': ['INBOX']}
        ).execute()
        print(f"Archived Gmail message {gmail_id}: {resp}")
    except Exception as e:
        # If the error is 'notFound', treat as non-fatal (already archived or deleted)
        if 'not found' in str(e).lower() or 'notfound' in str(e).lower():
            print(f"Gmail message {gmail_id} not found (may already be archived or deleted). Treating as non-fatal.")
        else:
            print(f"Failed to archive Gmail message {gmail_id}: {e}")


def get_latest_history_id(service) -> str:
    # Get the latest historyId from Gmail profile
    profile = service.users().getProfile(userId='me').execute()
    return profile.get('historyId')


def get_new_message_ids(service, last_history_id: str) -> list:
    # Use Gmail history API to get new message IDs since last_history_id
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
                msg_id = msg['message']['id']
                new_message_ids.add(msg_id)
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
            print(f"No categories found for user: {user_token.email}. Skipping processing.")
            return []

        # All users should have a history ID from when they first connected
        # If somehow they don't, set it up now
        if not last_history_id:
            print("No last_history_id found - this shouldn't happen in production. Setting up now.")
            from services.fake_db import set_history_id_by_email
            current_history_id = get_latest_history_id(service)
            set_history_id_by_email(user_token.email, current_history_id)
            print(f"Set initial history_id for {user_token.email} to {current_history_id}")
            return []  # Don't process any emails on first setup
        
        # Process new messages since last known history_id
        new_message_ids = get_new_message_ids(service, last_history_id)
        print(f"Found {len(new_message_ids)} new messages for {user_token.email}")

        processed = []

        for gmail_id in new_message_ids[:max_emails]:
            try:
                if email_exists(user_token.email, gmail_id):
                    print(f"Email {gmail_id} already processed for {user_token.email}")
                    continue
                msg_detail = service.users().messages().get(userId='me', id=gmail_id, format='full').execute()
                label_ids = msg_detail.get('labelIds', [])
                if 'INBOX' not in label_ids or 'SENT' in label_ids or 'DRAFT' in label_ids:
                    print(f"Skipping message {gmail_id}: not a received inbox message.")
                    continue
                headers = {h['name']: h['value'] for h in msg_detail['payload'].get('headers', [])}
                subject = headers.get('Subject', '')
                sender = headers.get('From', '')
                recipient = headers.get('To', '') or headers.get('Delivered-To', '')
                snippet = msg_detail.get('snippet', '')
                body = ''
                parts = msg_detail['payload'].get('parts', [])
                for part in parts:
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
                    id=0,
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
                print(f"Saved email: {subject} for {user_token.email} (category_id: {category_id})")
                archive_gmail_message(service, gmail_id)
                processed.append(email_obj.model_dump())
            except Exception as e:
                print(f"Error processing message {gmail_id} for {user_token.email}: {e}")
                continue

        return processed

    except Exception as e:
        print(f"Error in process_user_emails for {user_token.email}: {e}")
        raise e
