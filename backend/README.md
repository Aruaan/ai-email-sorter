# AI Email Sorter Backend

A FastAPI backend for an AI-powered email sorting application that automatically categorizes and summarizes emails using OpenAI.

## Features

- Google OAuth authentication
- Multi-account Gmail support
- AI-powered email classification and summarization
- Automatic email archiving
- Webhook-based real-time email processing
- Unsubscribe link extraction

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env`:
```bash
OPENAI_API_KEY=your_openai_api_key
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
FRONTEND_URL=http://localhost:3000
GMAIL_PUBSUB_TOPIC=projects/your-project/topics/gmail-notifications
GMAIL_WEBHOOK_URL=https://your-domain.com/gmail/webhook
```

3. Run the server:
```bash
python main.py
```

## Gmail Watch Setup

The app automatically sets up Gmail watch when users first connect their accounts. This enables real-time email processing via webhooks.

### Required Environment Variables:
- `GMAIL_PUBSUB_TOPIC`: Your Google Cloud Pub/Sub topic for Gmail notifications
- `GMAIL_WEBHOOK_URL`: Your webhook endpoint URL

### How it works:
1. When a user first signs in with Google, the app:
   - Gets the current Gmail history ID
   - Sets up Gmail watch for the INBOX
   - Stores the history ID in the database
2. When new emails arrive, Gmail sends webhooks to your endpoint
3. The app processes new emails since the last known history ID
4. Emails are classified, summarized, and archived automatically

## API Endpoints

- `GET /auth/google` - Google OAuth login
- `GET /auth/callback` - OAuth callback
- `GET /auth/session/{session_id}` - Get session info
- `POST /categories/` - Create category
- `GET /categories/` - List categories
- `GET /emails/` - List emails by category
- `POST /emails/unsubscribe` - Extract unsubscribe links
- `POST /gmail/webhook` - Gmail webhook endpoint

## Testing

Run tests with:
```bash
pytest tests/
``` 