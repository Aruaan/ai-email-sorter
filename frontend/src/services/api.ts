import axios from 'axios';
import { Category, Email, UnsubscribeResult, SessionInfo } from '../types';

const BASE_URL = "https://ai-email-sorter-5mom.onrender.com"

const api = axios.create({
  baseURL: BASE_URL || 'http://localhost:8000',
  timeout: 60000, // Increased from 10000 to 60000 (60 seconds)
});

// Auth API
export const authAPI = {
  googleLogin: () => {
    window.location.href = `${BASE_URL}/auth/google`;
  },
  googleCallback: (code: string, state: string) => {
    return api.get(`/auth/callback?code=${code}&state=${state}`);
  },
  addAccount: (sessionId: string) => {
    window.location.href = `${BASE_URL}/auth/google/add-account?session_id=${sessionId}`;
  },
  getSessionInfo: async (sessionId: string): Promise<SessionInfo> => {
    const res = await api.get(`/auth/session/${sessionId}`);
    return res.data;
  },
  setPrimaryAccount: (sessionId: string, email: string) => {
    return api.post(`/auth/session/${sessionId}/primary?email=${email}`);
  }
};

// Categories API
export const categoriesAPI = {
  getCategories: async (sessionId: string): Promise<Category[]> => {
    const res = await api.get(`/categories/?session_id=${sessionId}`);
    return res.data;
  },
  createCategory: async (name: string, description: string, sessionId: string): Promise<Category> => {
    const res = await api.post('/categories/', { name, description, session_id: sessionId });
    return res.data;
  },
  updateCategory: async (categoryId: string, name?: string, description?: string): Promise<any> => {
    const payload: any = {};
    if (name !== undefined) payload.name = name;
    if (description !== undefined) payload.description = description;
    const res = await api.put(`/categories/${categoryId}`, payload);
    return res.data;
  }
};

// Emails API
export const emailsAPI = {
  getEmails: async (sessionId: string, categoryId: string, userEmail?: string): Promise<Email[]> => {
    const params = new URLSearchParams({ 
      session_id: sessionId, 
      category_id: categoryId
    });
    if (userEmail) {
      params.append('user_email', userEmail);
    }
    const res = await api.get(`/emails/?${params}`);
    return res.data;
  },
  getUnsubscribeLinks: async (emailIds: string[]): Promise<UnsubscribeResult[]> => {
    const res = await api.post('/emails/unsubscribe', emailIds);
    return res.data;
  },
  processEmails: async (sessionId: string, email?: string, maxEmails: number = 2) => {
    const params = new URLSearchParams({ session_id: sessionId, max_emails: maxEmails.toString() });
    if (email) params.append('email', email);
    const res = await api.get(`/dev/process-emails?${params}`);
    return res.data;
  },
  aiUnsubscribe: async (unsubscribeLinks: string[], userEmail?: string) => {
    const res = await api.post('/emails/unsubscribe/ai', {
      unsubscribe_links: unsubscribeLinks,
      user_email: userEmail,
    });
    return res.data;
  },
  deleteEmails: async (emailIds: string[]): Promise<any> => {
    const res = await api.delete('/emails/', { data: emailIds });
    return res.data;
  }
};

// Session Management API
export const sessionAPI = {
  getSessionAccounts: async (sessionId: string) => {
    const res = await api.get(`/dev/session/${sessionId}/accounts`);
    return res.data;
  },
  removeAccount: async (sessionId: string, email: string) => {
    const res = await api.delete(`/auth/session/${sessionId}/account?email=${encodeURIComponent(email)}`);
    return res.data;
  }
}; 