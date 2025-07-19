import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, LogOut, Trash2, Mail, ExternalLink, X } from 'lucide-react'
import { emailsAPI } from '../services/api'
import { Email, UnsubscribeResult } from '../types'

interface CategoryViewProps {
  userEmail: string
  onLogout: () => void
}

const CategoryView = ({ userEmail, onLogout }: CategoryViewProps) => {
  const { categoryId } = useParams<{ categoryId: string }>()
  const [emails, setEmails] = useState<Email[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedEmails, setSelectedEmails] = useState<Set<number>>(new Set())
  const [unsubscribeResults, setUnsubscribeResults] = useState<UnsubscribeResult[]>([])
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null)
  const [showEmailModal, setShowEmailModal] = useState(false)

  useEffect(() => {
    if (categoryId) {
      loadEmails(parseInt(categoryId))
    }
  }, [categoryId])

  const loadEmails = async (categoryId: number) => {
    try {
      const data = await emailsAPI.getEmails(userEmail, categoryId)
      setEmails(data)
    } catch (error) {
      console.error('Failed to load emails:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSelectEmail = (emailId: number) => {
    const newSelected = new Set(selectedEmails)
    if (newSelected.has(emailId)) {
      newSelected.delete(emailId)
    } else {
      newSelected.add(emailId)
    }
    setSelectedEmails(newSelected)
  }

  const handleSelectAll = () => {
    if (selectedEmails.size === emails.length) {
      setSelectedEmails(new Set())
    } else {
      setSelectedEmails(new Set(emails.map(email => email.id)))
    }
  }

  const handleUnsubscribe = async () => {
    if (selectedEmails.size === 0) return

    try {
      const results = await emailsAPI.getUnsubscribeLinks(Array.from(selectedEmails))
      setUnsubscribeResults(results)
      
      // Open unsubscribe links in new tabs
      results.forEach(result => {
        result.unsubscribe_links.forEach(link => {
          if (link.startsWith('http')) {
            window.open(link, '_blank')
          } else if (link.startsWith('mailto:')) {
            window.location.href = link
          }
        })
      })
    } catch (error) {
      console.error('Failed to get unsubscribe links:', error)
    }
  }

  const handleDelete = () => {
    // Stub for delete functionality
    console.log('Deleting emails:', Array.from(selectedEmails))
    alert('Delete functionality will be implemented later')
  }

  const handleEmailClick = (email: Email) => {
    setSelectedEmail(email)
    setShowEmailModal(true)
  }

  const closeEmailModal = () => {
    setShowEmailModal(false)
    setSelectedEmail(null)
  }

  const handleModalBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeEmailModal()
    }
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && showEmailModal) {
      closeEmailModal()
    }
  }

  useEffect(() => {
    if (showEmailModal) {
      document.addEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'hidden' // Prevent background scrolling
    } else {
      document.body.style.overflow = 'unset'
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.body.style.overflow = 'unset'
    }
  }, [showEmailModal])

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading emails...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Link
                to="/"
                className="flex items-center text-gray-600 hover:text-gray-900 mr-4"
              >
                <ArrowLeft className="w-5 h-5 mr-2" />
                Back to Categories
              </Link>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">Category Emails</h1>
                <p className="text-sm text-gray-600">{userEmail}</p>
              </div>
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
        <div className="px-4 py-6 sm:px-0">
          {/* Bulk Actions */}
          {emails.length > 0 && (
            <div className="mb-6 bg-white rounded-lg shadow p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={selectedEmails.size === emails.length}
                      onChange={handleSelectAll}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <span className="ml-2 text-sm text-gray-700">
                      Select All ({selectedEmails.size}/{emails.length})
                    </span>
                  </label>
                </div>
                {selectedEmails.size > 0 && (
                  <div className="flex space-x-3">
                    <button
                      onClick={handleUnsubscribe}
                      className="flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-green-600 hover:bg-green-700"
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Unsubscribe ({selectedEmails.size})
                    </button>
                    <button
                      onClick={handleDelete}
                      className="flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700"
                    >
                      <Trash2 className="w-4 h-4 mr-2" />
                      Delete ({selectedEmails.size})
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Emails List */}
          <div className="space-y-4">
            {emails.map((email) => (
              <div
                key={email.id}
                className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => handleEmailClick(email)}
              >
                <div className="flex items-start space-x-4">
                  <input
                    type="checkbox"
                    checked={selectedEmails.has(email.id)}
                    onChange={(e) => {
                      e.stopPropagation()
                      handleSelectEmail(email.id)
                    }}
                    className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-lg font-medium text-gray-900 mb-2">
                          {email.subject}
                        </h3>
                        <p className="text-sm text-gray-600 mb-2">
                          From: {email.from_email}
                        </p>
                        <p className="text-gray-700">{email.summary}</p>
                      </div>
                      <Mail className="w-5 h-5 text-gray-400 flex-shrink-0 ml-4" />
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {emails.length === 0 && (
            <div className="text-center py-12">
              <Mail className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No emails</h3>
              <p className="mt-1 text-sm text-gray-500">
                No emails have been sorted into this category yet.
              </p>
            </div>
          )}

          {/* Unsubscribe Results */}
          {unsubscribeResults.length > 0 && (
            <div className="mt-6 bg-blue-50 rounded-lg p-4">
              <h3 className="text-lg font-medium text-blue-900 mb-2">
                Unsubscribe Results
              </h3>
              <div className="space-y-2">
                {unsubscribeResults.map((result) => (
                  <div key={result.email_id} className="text-sm">
                    <span className="font-medium">Email {result.email_id}:</span>
                    {result.error ? (
                      <span className="text-red-600 ml-2">{result.error}</span>
                    ) : (
                      <span className="text-green-600 ml-2">
                        {result.unsubscribe_links.length} unsubscribe link(s) found
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Email Modal */}
      {showEmailModal && selectedEmail && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
          onClick={handleModalBackgroundClick}
        >
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-hidden">
            <div className="flex items-center justify-between p-6 border-b">
              <h2 className="text-xl font-semibold text-gray-900">Email Details</h2>
              <button
                onClick={closeEmailModal}
                className="text-gray-400 hover:text-gray-600"
              >
                <X className="w-6 h-6" />
              </button>
            </div>
            <div className="p-6 overflow-y-auto max-h-[calc(90vh-120px)]">
              <div className="space-y-4">
                <div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">
                    {selectedEmail.subject}
                  </h3>
                  <p className="text-sm text-gray-600">
                    From: {selectedEmail.from_email}
                  </p>
                </div>
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Summary</h4>
                  <p className="text-gray-700 mb-4">{selectedEmail.summary}</p>
                </div>
                <div className="border-t pt-4">
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Full Content</h4>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                      {selectedEmail.raw}
                    </pre>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default CategoryView 