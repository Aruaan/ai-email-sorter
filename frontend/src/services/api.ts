import axios from 'axios'
import { Category, Email, UnsubscribeResult } from '../types'

const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

export const authAPI = {
  googleLogin: () => {
    window.location.href = `${API_BASE_URL}/auth/google`
  },
  
  googleCallback: async (code: string, state: string) => {
    const response = await api.get(`/auth/callback?code=${code}&state=${state}`)
    return response.data
  }
}

export const categoriesAPI = {
  getCategories: async (userEmail: string): Promise<Category[]> => {
    const response = await api.get(`/categories/?user_email=${encodeURIComponent(userEmail)}`)
    return response.data
  },

  createCategory: async (name: string, description: string, userEmail: string): Promise<Category> => {
    const response = await api.post('/categories/', {
      name,
      description,
      user_email: userEmail
    })
    return response.data
  }
}

export const emailsAPI = {
  getEmails: async (userEmail: string, categoryId: number): Promise<Email[]> => {
    const response = await api.get(`/emails/?user_email=${encodeURIComponent(userEmail)}&category_id=${categoryId}`)
    return response.data
  },

  getUnsubscribeLinks: async (emailIds: number[]): Promise<UnsubscribeResult[]> => {
    const response = await api.post('/emails/unsubscribe', emailIds)
    return response.data
  },

  processEmails: async (userEmail: string, maxEmails: number = 5): Promise<any[]> => {
    const response = await api.get(`/dev/process-emails?user_email=${encodeURIComponent(userEmail)}&max_emails=${maxEmails}`)
    return response.data
  }
}

export default api 