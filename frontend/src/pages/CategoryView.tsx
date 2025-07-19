import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { ArrowLeft, LogOut, Trash2, Mail, ExternalLink, X, CheckSquare, Square } from 'lucide-react'
import { emailsAPI } from '../services/api'
import { Email, UnsubscribeResult, SessionInfo } from '../types'
import { useAccount } from '../contexts/AccountContext'

interface CategoryViewProps {
  userEmail: string;
  sessionId: string;
  sessionInfo: SessionInfo | null;
}

const CategoryView = ({ userEmail, sessionId, sessionInfo }: CategoryViewProps) => {
  const { categoryId } = useParams<{ categoryId: string }>();
  const navigate = useNavigate();
  const { activeAccount } = useAccount();
  const [emails, setEmails] = useState<Email[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEmails, setSelectedEmails] = useState<Set<number>>(new Set());
  const [unsubscribeResults, setUnsubscribeResults] = useState<UnsubscribeResult[]>([]);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);

  useEffect(() => {
    if (categoryId) {
      loadEmails();
    }
  }, [categoryId, userEmail]);

  const loadEmails = async () => {
    if (!categoryId) return;
    
    try {
      setIsLoading(true);
      const data = await emailsAPI.getEmails(userEmail, parseInt(categoryId));
      setEmails(data);
    } catch (error) {
      console.error('Failed to load emails:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectEmail = (emailId: number) => {
    const newSelected = new Set(selectedEmails);
    if (newSelected.has(emailId)) {
      newSelected.delete(emailId);
    } else {
      newSelected.add(emailId);
    }
    setSelectedEmails(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedEmails.size === emails.length) {
      setSelectedEmails(new Set());
    } else {
      setSelectedEmails(new Set(emails.map(email => email.id)));
    }
  };

  const handleUnsubscribe = async () => {
    if (selectedEmails.size === 0) return;

    try {
      const results = await emailsAPI.getUnsubscribeLinks(Array.from(selectedEmails));
      setUnsubscribeResults(results);
      
      // Open unsubscribe links in new tabs
      results.forEach(result => {
        result.unsubscribe_links.forEach(link => {
          window.open(link, '_blank');
        });
      });
      
      // Clear selection after unsubscribe
      setSelectedEmails(new Set());
    } catch (error) {
      console.error('Failed to get unsubscribe links:', error);
    }
  };

  const handleDelete = () => {
    alert('Delete functionality will be implemented in the next update.');
  };

  const openEmailModal = (email: Email) => {
    setSelectedEmail(email);
    setShowEmailModal(true);
  };

  const closeEmailModal = () => {
    setShowEmailModal(false);
    setSelectedEmail(null);
  };

  const handleModalBackgroundClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeEmailModal();
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Escape' && showEmailModal) {
      closeEmailModal();
    }
  };

  useEffect(() => {
    if (showEmailModal) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [showEmailModal]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading emails...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/')}
                className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
              >
                <ArrowLeft className="w-5 h-5" />
                <span>Back to Dashboard</span>
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Category Emails</h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">
                {sessionInfo?.accounts.length || 0} Accounts
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Bulk Actions */}
        {selectedEmails.size > 0 && (
          <div className="bg-white shadow rounded-lg p-4 mb-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-700">
                {selectedEmails.size} email(s) selected
              </span>
              <div className="flex space-x-3">
                <button
                  onClick={handleUnsubscribe}
                  className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100"
                >
                  <ExternalLink className="w-4 h-4" />
                  <span>Unsubscribe</span>
                </button>
                <button
                  onClick={handleDelete}
                  className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-md hover:bg-red-100"
                >
                  <Trash2 className="w-4 h-4" />
                  <span>Delete</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Unsubscribe Results */}
        {unsubscribeResults.length > 0 && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <h3 className="text-sm font-medium text-green-800 mb-2">Unsubscribe Results</h3>
            {unsubscribeResults.map((result, index) => (
              <div key={index} className="text-sm text-green-700">
                {result.unsubscribe_links.length > 0 ? (
                  <div>
                    Email {result.email_id}: {result.unsubscribe_links.length} unsubscribe link(s) opened
                  </div>
                ) : (
                  <div>Email {result.email_id}: No unsubscribe links found</div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Emails List */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">Emails</h2>
              {emails.length > 0 && (
                <button
                  onClick={handleSelectAll}
                  className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-800"
                >
                  {selectedEmails.size === emails.length ? (
                    <CheckSquare className="w-4 h-4" />
                  ) : (
                    <Square className="w-4 h-4" />
                  )}
                  <span>
                    {selectedEmails.size === emails.length ? 'Deselect All' : 'Select All'}
                  </span>
                </button>
              )}
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {emails.length === 0 ? (
              <div className="px-6 py-8 text-center">
                <Mail className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No emails</h3>
                <p className="mt-1 text-sm text-gray-500">
                  No emails found in this category.
                </p>
              </div>
            ) : (
              emails.map((email) => (
                <div
                  key={email.id}
                  className="px-6 py-4 hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-start space-x-3">
                    <button
                      onClick={() => handleSelectEmail(email.id)}
                      className="mt-1"
                    >
                      {selectedEmails.has(email.id) ? (
                        <CheckSquare className="w-4 h-4 text-blue-600" />
                      ) : (
                        <Square className="w-4 h-4 text-gray-400" />
                      )}
                    </button>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <h3 className="text-sm font-medium text-gray-900 truncate">
                          {email.subject}
                        </h3>
                        <button
                          onClick={() => openEmailModal(email)}
                          className="text-sm text-blue-600 hover:text-blue-800"
                        >
                          View
                        </button>
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        From: {email.from_email}
                      </p>
                      <p className="text-sm text-gray-500 mt-1">
                        {email.summary}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>

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
                  <h3 className="text-lg font-medium text-gray-900">{selectedEmail.subject}</h3>
                  <p className="text-sm text-gray-600 mt-1">From: {selectedEmail.from_email}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Summary</h4>
                  <p className="text-sm text-gray-700">{selectedEmail.summary}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Content</h4>
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap bg-gray-50 p-4 rounded-md overflow-x-auto">
                    {selectedEmail.raw}
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoryView; 