import axios from 'axios';
import { Category, Email, UnsubscribeResult, SessionInfo } from '../types';

const api = axios.create({
  baseURL: '/api',
  timeout: 60000, // Increased from 10000 to 60000 (60 seconds)
});

// Auth API
export const authAPI = {
  googleLogin: () => {
    window.location.href = '/api/auth/google';
  },
  googleCallback: (code: string, state: string) => {
    return api.get(`/auth/callback?code=${code}&state=${state}`);
  },
  addAccount: (sessionId: string) => {
    window.location.href = `/api/auth/google/add-account?session_id=${sessionId}`;
  },
  getSessionInfo: (sessionId: string): Promise<SessionInfo> => {
    return api.get(`/auth/session/${sessionId}`).then(res => res.data);
  },
  setPrimaryAccount: (sessionId: string, email: string) => {
    return api.post(`/auth/session/${sessionId}/primary?email=${email}`);
  }
};

// Categories API
export const categoriesAPI = {
  getCategories: (userEmail: string): Promise<Category[]> => {
    return api.get(`/categories/?user_email=${userEmail}`).then(res => res.data);
  },
  createCategory: (name: string, description: string, userEmail: string): Promise<Category> => {
    return api.post('/categories/', { name, description, user_email: userEmail }).then(res => res.data);
  }
};

// Emails API
export const emailsAPI = {
  getEmails: (userEmail: string, categoryId: number): Promise<Email[]> => {
    return api.get(`/emails/?user_email=${userEmail}&category_id=${categoryId}`).then(res => res.data);
  },
  getUnsubscribeLinks: (emailIds: number[]): Promise<UnsubscribeResult[]> => {
    return api.post('/emails/unsubscribe', emailIds).then(res => res.data);
  },
  processEmails: (sessionId: string, email?: string, maxEmails: number = 2) => {
    const params = new URLSearchParams({ session_id: sessionId, max_emails: maxEmails.toString() });
    if (email) params.append('email', email);
    return api.get(`/dev/process-emails?${params}`).then(res => res.data);
  }
};

// Session Management API
export const sessionAPI = {
  getSessionAccounts: (sessionId: string) => {
    return api.get(`/dev/session/${sessionId}/accounts`).then(res => res.data);
  }
}; 