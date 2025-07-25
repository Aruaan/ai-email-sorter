# AI Email Sorter

A full-stack application for AI-powered Gmail sorting, bulk actions, and smart unsubscribe.

## Features
- **Google OAuth Sign-in**: Secure login with your Google account.
- **Custom Categories**: Organize emails with your own categories and descriptions.
- **AI Email Processing**: Incoming emails are auto-sorted and summarized using OpenAI.
- **Category View**: See all emails in a category, with AI summaries.
- **Bulk Actions**: Select multiple emails to delete or unsubscribe.
- **AI Unsubscribe**: Automated browser agent finds and completes unsubscribe flows.
- **Original Email Content**: View the full content of any email.
- **Multi-Inbox Support**: Connect and manage multiple Gmail accounts.
- **Robust Testing**: Backend and frontend tests included.

---

## Project Structure

```
ai-email-sorter/
  backend/    # FastAPI, Python, PostgreSQL, OpenAI, Playwright
  frontend/   # React, Vite, TypeScript, Tailwind CSS
```

---

## Backend (FastAPI, Python)

### Setup
1. **Python 3.9+** and **PostgreSQL** required.
2. `cd backend`
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   playwright install
   ```
4. Copy `.env.example` to `.env` and fill in:
   - Google OAuth credentials
   - OpenAI API key
   - PostgreSQL connection info
   - (Optional) Render/Cloud deployment variables

### Running Locally
```sh
uvicorn backend.main:app --reload
```
- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Testing
```sh
pytest
```

### Deployment
- Dockerfile included (see `backend/Dockerfile`).
- Designed for Render.com, but works on any Docker host.

---

## Frontend (React, Vite, TypeScript)

### Setup
1. `cd frontend`
2. Install dependencies:
   ```sh
   npm install
   ```
3. (Optional) Set environment variables in `.env` if needed (e.g., API base URL).

### Running Locally
```sh
npm run dev
```
- App: [http://localhost:5173](http://localhost:5173)

### Testing
```sh
npm test
```

### Deployment
- Vercel configuration included (`vercel.json`).
- Deploy to Vercel or any static host.

---

## Environment Variables
- **Backend**: See `backend/.env.example` for all required variables (Google, OpenAI, DB, etc).
- **Frontend**: Set `VITE_API_URL` if you want to override the backend URL.

---

## Main Technologies
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, OpenAI, Playwright, Google API
- **Frontend**: React, Vite, TypeScript, Tailwind CSS

