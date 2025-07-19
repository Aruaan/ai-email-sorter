# AI Email Sorter Frontend

A React + TypeScript + TailwindCSS frontend for the AI Email Sorter application.

## Features

- **Google OAuth Sign-in**: Secure authentication with Google
- **Category Management**: Create and view email categories
- **Email Viewing**: Browse emails by category with AI summaries
- **Bulk Actions**: Select multiple emails for unsubscribe or delete operations
- **Unsubscribe Integration**: Extract and open unsubscribe links automatically

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **TailwindCSS** for styling
- **React Router** for navigation
- **Axios** for API communication
- **Lucide React** for icons

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start the development server**:
   ```bash
   npm run dev
   ```

3. **Build for production**:
   ```bash
   npm run build
   ```

## Development

The frontend runs on `http://localhost:3000` and proxies API requests to the backend at `http://localhost:8000`.

### Project Structure

```
src/
├── components/          # Reusable UI components
├── pages/              # Page components
│   ├── Login.tsx       # Google OAuth login
│   ├── Dashboard.tsx   # Categories overview
│   └── CategoryView.tsx # Email list by category
├── services/           # API services
│   └── api.ts         # Backend API communication
├── types/              # TypeScript type definitions
│   └── index.ts       # Data models
├── App.tsx            # Main app with routing
└── main.tsx           # Entry point
```

### Key Features

1. **Authentication Flow**:
   - User clicks "Sign in with Google"
   - Redirects to backend OAuth endpoint
   - Backend handles Google OAuth and stores user token
   - Frontend stores user email in localStorage

2. **Category Management**:
   - View all categories for the user
   - Create new categories with name and description
   - Click categories to view emails

3. **Email Management**:
   - View emails by category with AI summaries
   - Select individual or all emails
   - Bulk unsubscribe: extracts links and opens them
   - Bulk delete (stubbed for now)

4. **Unsubscribe Integration**:
   - Calls backend to extract unsubscribe links
   - Opens HTTP links in new tabs
   - Opens mailto: links in default email client
   - Shows results to user

## API Integration

The frontend communicates with the FastAPI backend through:

- `/api/auth/google` - Google OAuth redirect
- `/api/categories/` - Category CRUD operations
- `/api/emails/` - Email listing and operations

## Environment Variables

No environment variables are needed for the frontend - it uses the proxy configuration in `vite.config.ts` to communicate with the backend.

## Next Steps

- Add email detail view to read full email content
- Implement actual delete functionality
- Add email processing/import functionality
- Add multi-account support
- Add persistent database integration
