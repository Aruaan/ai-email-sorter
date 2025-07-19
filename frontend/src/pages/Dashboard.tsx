import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Plus, LogOut, Mail, RefreshCw } from 'lucide-react'
import { categoriesAPI, emailsAPI } from '../services/api'
import { Category } from '../types'

interface DashboardProps {
  userEmail: string
  onLogout: () => void
}

const Dashboard = ({ userEmail, onLogout }: DashboardProps) => {
  const [categories, setCategories] = useState<Category[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newCategory, setNewCategory] = useState({ name: '', description: '' })
  const [isProcessingEmails, setIsProcessingEmails] = useState(false)
  const [processingStatus, setProcessingStatus] = useState<string>('')
  const [emailCounts, setEmailCounts] = useState<Record<number, number>>({})

  useEffect(() => {
    loadCategories()
  }, [])

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.getCategories(userEmail)
      setCategories(data)
      
      // Load email counts for each category
      const counts: Record<number, number> = {}
      for (const category of data) {
        try {
          const emails = await emailsAPI.getEmails(userEmail, category.id)
          counts[category.id] = emails.length
        } catch (error) {
          counts[category.id] = 0
        }
      }
      setEmailCounts(counts)
    } catch (error) {
      console.error('Failed to load categories:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newCategory.name.trim()) return

    try {
      const category = await categoriesAPI.createCategory(
        newCategory.name,
        newCategory.description,
        userEmail
      )
      setCategories([...categories, category])
      setNewCategory({ name: '', description: '' })
      setShowCreateForm(false)
    } catch (error) {
      console.error('Failed to create category:', error)
    }
  }

  const handleProcessEmails = async () => {
    if (categories.length === 0) {
      alert('Please create at least one category before processing emails.')
      return
    }

    setIsProcessingEmails(true)
    setProcessingStatus('Processing emails...')

    try {
      const results = await emailsAPI.processEmails(userEmail, 5)
      setProcessingStatus(`Successfully processed ${results.length} emails!`)
      
      // Refresh categories to show updated email counts
      setTimeout(() => {
        loadCategories()
        setProcessingStatus('')
      }, 2000)
    } catch (error) {
      console.error('Failed to process emails:', error)
      setProcessingStatus('Failed to process emails. Please try again.')
    } finally {
      setIsProcessingEmails(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading categories...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">AI Email Sorter</h1>
              <p className="text-sm text-gray-600">{userEmail}</p>
            </div>
            <button
              onClick={onLogout}
              className="flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Email Processing Section */}
        <div className="px-4 py-6 sm:px-0">
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-medium text-gray-900">Email Processing</h2>
                <p className="text-sm text-gray-600">
                  Process and categorize your Gmail inbox using AI
                </p>
              </div>
              <button
                onClick={handleProcessEmails}
                disabled={isProcessingEmails || categories.length === 0}
                className="flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {isProcessingEmails ? (
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Mail className="w-4 h-4 mr-2" />
                )}
                {isProcessingEmails ? 'Processing...' : 'Process Emails'}
              </button>
            </div>
            {processingStatus && (
              <div className="mt-4 p-3 bg-blue-50 rounded-md">
                <p className="text-sm text-blue-800">{processingStatus}</p>
              </div>
            )}
          </div>

          {/* Categories Section */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-gray-900">Categories</h2>
            <button
              onClick={() => setShowCreateForm(true)}
              className="flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Add Category
            </button>
          </div>

          {/* Create Category Form */}
          {showCreateForm && (
            <div className="mb-6 p-4 bg-white rounded-lg shadow">
              <form onSubmit={handleCreateCategory} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Category Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={newCategory.name}
                    onChange={(e) => setNewCategory({ ...newCategory, name: e.target.value })}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    id="description"
                    value={newCategory.description}
                    onChange={(e) => setNewCategory({ ...newCategory, description: e.target.value })}
                    rows={3}
                    className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Describe what types of emails should go in this category..."
                  />
                </div>
                <div className="flex space-x-3">
                  <button
                    type="submit"
                    className="px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                  >
                    Create Category
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowCreateForm(false)}
                    className="px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Categories Grid */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {categories.map((category) => (
              <Link
                key={category.id}
                to={`/category/${category.id}`}
                className="block p-6 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Mail className="w-8 h-8 text-blue-600" />
                    <div className="ml-4">
                      <h3 className="text-lg font-medium text-gray-900">{category.name}</h3>
                      {category.description && (
                        <p className="text-sm text-gray-600 mt-1">{category.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                      {emailCounts[category.id] || 0} emails
                    </span>
                  </div>
                </div>
              </Link>
            ))}
          </div>

          {categories.length === 0 && (
            <div className="text-center py-12">
              <Mail className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No categories</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating your first category.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default Dashboard 