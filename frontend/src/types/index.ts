export interface Category {
  id: number
  name: string
  description?: string
  user_email: string
}

export interface Email {
  id: number
  subject: string
  from_email: string
  category_id: number
  summary: string
  raw: string
  user_email: string
  gmail_id: string
  headers?: Record<string, string>
}

export interface UnsubscribeResult {
  email_id: number
  unsubscribe_links: string[]
  error?: string
} 