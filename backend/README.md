# Backend Setup

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Set up environment variables

Copy `.env.example` to `.env` and fill in your Google OAuth credentials:

```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/callback
PORT=8000
```

## 3. Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
``` 