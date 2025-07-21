export interface Category {
  id: string
  name: string
  description?: string
  session_id: string
}

export interface Email {
  id: string
  subject: string
  from_email: string
  category_id: string
  summary: string
  raw: string
  user_email: string
  gmail_id: string
  headers?: Record<string, string>
}

export interface UnsubscribeResult {
  email_id: string
  unsubscribe_links: string[]
  error?: string
}

export interface UserToken {
  email: string;
  access_token: string;
  refresh_token?: string;
}

export interface UserSession {
  session_id: string;
  accounts: UserToken[];
  primary_account: string;
}

export interface SessionInfo {
  session_id: string;
  accounts: { email: string }[];
  primary_account: string;
} 