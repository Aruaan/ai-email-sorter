import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, Trash2, Mail, ExternalLink, X, CheckSquare, Square, RefreshCw, CheckCircle, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react'
import { emailsAPI, categoriesAPI } from '../services/api'
import { Email, UnsubscribeResult, SessionInfo } from '../types'
import { useAccount } from '../contexts/AccountContext'

interface CategoryViewProps {
  userEmail: string;
  sessionId: string;
  sessionInfo: SessionInfo | null;
}

const CategoryView = ({ sessionId, sessionInfo }: CategoryViewProps) => {
  const { categoryId } = useParams<{ categoryId: string }>();
  const navigate = useNavigate();
  const { activeAccount } = useAccount();
  const [emails, setEmails] = useState<Email[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedEmails, setSelectedEmails] = useState<Set<string>>(new Set());
  const [unsubscribeResults, setUnsubscribeResults] = useState<UnsubscribeResult[]>([]);
  const [aiUnsubscribeResults, setAiUnsubscribeResults] = useState<any[]>([]);
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastTimeout, setToastTimeout] = useState<number | null>(null);
  const [categoryName, setCategoryName] = useState<string>('');
  const [categoryDescription, setCategoryDescription] = useState<string>('');
  const [unsubscribeDropdownOpen, setUnsubscribeDropdownOpen] = useState(false);
  const [unsubscribeCheckedCount, setUnsubscribeCheckedCount] = useState(0);

  useEffect(() => {
    if (categoryId) {
      loadEmails();
      loadCategoryInfo();
    }
  }, [categoryId, sessionId, activeAccount]);

  const loadCategoryInfo = async () => {
    if (!categoryId) return;
    
    try {
      const categories = await categoriesAPI.getCategories(sessionId);
      const category = categories.find((cat: any) => cat.id === categoryId);
      if (category) {
        setCategoryName(category.name);
        setCategoryDescription(category.description || '');
      }
    } catch (error) {
      console.error('Failed to load category info:', error);
    }
  };

  const loadEmails = async () => {
    if (!categoryId) return;
    
    try {
      setIsLoading(true);
      // Use activeAccount for filtering, but handle "All Accounts" case and single account case
      // If activeAccount is empty, "All Accounts", or there's only one account, don't filter
      const userEmail = (activeAccount && activeAccount !== 'All Accounts' && sessionInfo?.accounts && sessionInfo.accounts.length > 1) ? activeAccount : undefined;
      
      console.log('[CategoryView] Loading emails with:', {
        sessionId,
        categoryId,
        userEmail,
        activeAccount,
        accountsCount: sessionInfo?.accounts?.length
      });
      
      const data = await emailsAPI.getEmails(sessionId, categoryId, userEmail);
      
      console.log('[CategoryView] Loaded emails:', {
        count: data.length,
        emails: data.map(e => ({ id: e.id, subject: e.subject, user_email: e.user_email }))
      });
      
      setEmails(data);
      // setToastMessage(`Loaded ${data.length} email(s) in this category.`); // Removed toast
      if (toastTimeout) clearTimeout(toastTimeout);
      const timeout = window.setTimeout(() => setToastMessage(null), 3000);
      setToastTimeout(timeout);
    } catch (error) {
      console.error('Failed to load emails:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelectEmail = (emailId: string) => {
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
      // Get unsubscribe links for selected emails
      const results = await emailsAPI.getUnsubscribeLinks(Array.from(selectedEmails));
      setUnsubscribeResults(results);
      setUnsubscribeCheckedCount(selectedEmails.size); // Store count for label
      setUnsubscribeDropdownOpen(false); // Collapse by default after action

      // Collect all unsubscribe links from all selected emails
      const allLinks = results.flatMap(result => result.unsubscribe_links);
      if (allLinks.length > 0) {
        // Call AI-powered unsubscribe endpoint
        const aiResult = await emailsAPI.aiUnsubscribe(allLinks, sessionInfo?.primary_account);
        setAiUnsubscribeResults(aiResult.results || []);
      } else {
        setAiUnsubscribeResults([]);
      }
      // Clear selection after unsubscribe
      setSelectedEmails(new Set());
    } catch (error) {
      console.error('Failed to get unsubscribe links or AI unsubscribe:', error);
      setUnsubscribeResults([]);
      setAiUnsubscribeResults([]);
    }
  };

  const handleDelete = async () => {
    if (selectedEmails.size === 0) return;
    
    if (!confirm(`Are you sure you want to delete ${selectedEmails.size} email(s)? This action cannot be undone.`)) {
      return;
    }

    try {
      const emailIds = Array.from(selectedEmails);
      const result = await emailsAPI.deleteEmails(emailIds);
      
      if (result.error) {
        setToastMessage(`Error: ${result.error}`);
      } else {
        setToastMessage(`Successfully deleted ${result.deleted_count} email(s)`);
        // Reload emails to reflect the changes
        await loadEmails();
        // Clear selection
        setSelectedEmails(new Set());
      }
      
      if (toastTimeout) clearTimeout(toastTimeout);
      const timeout = window.setTimeout(() => setToastMessage(null), 4000);
      setToastTimeout(timeout);
    } catch (error) {
      console.error('Failed to delete emails:', error);
      setToastMessage('Failed to delete emails. Please try again.');
      if (toastTimeout) clearTimeout(toastTimeout);
      const timeout = window.setTimeout(() => setToastMessage(null), 4000);
      setToastTimeout(timeout);
    }
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
  {/* Centered Header Section */}
  <div className="bg-white pt-8 pb-4 px-6 rounded-t-xl shadow-sm border-b border-gray-200">
    <div className="max-w-3xl mx-auto flex items-center space-x-4">
      <button
        onClick={() => navigate('/')}
        className="inline-flex items-center text-blue-600 hover:underline text-sm font-medium focus:outline-none focus:ring-2 focus:ring-blue-400"
        aria-label="Back to Dashboard"
        style={{ fontWeight: 500, padding: 0, background: 'none', border: 'none' }}
      >
        <ArrowLeft className="w-4 h-4 mr-1" /> Back
      </button>
      <div className="flex flex-col">
        <span className="text-xl font-semibold text-gray-900">{categoryName}</span>
        {categoryDescription && (
          <span className="text-sm text-gray-500">{categoryDescription}</span>
        )}
      </div>
    </div>
  </div>
  <div className="h-2 bg-gray-50" />

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Toast Banner */}
        {toastMessage && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-6 py-3 rounded shadow-lg z-50 transition-all">
            {toastMessage}
          </div>
        )}

        {/* Unified Category Card: Header, Emails List */}
        <div className="bg-white shadow rounded-xl p-6 mb-4 min-h-[500px] flex flex-col">
          {/* Single, clean header */}
          <div className="mb-2 flex items-center gap-2">
        
            
          </div>
          {/* Bulk Actions */}
          {selectedEmails.size > 0 && (
            <div className="sticky top-[70px] z-10 bg-blue-600 border-b border-blue-700 shadow-md rounded-b-xl px-6 py-3 flex items-center justify-between mb-4 animate-fade-in">
              <span className="text-white font-semibold">{selectedEmails.size} email(s) selected</span>
              <div className="flex gap-2">
                <button
                  onClick={handleUnsubscribe}
                  className="flex items-center gap-1 px-4 py-2 text-sm font-bold text-blue-700 bg-white border border-blue-300 rounded-lg shadow hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-blue-400"
                >
                  <ExternalLink className="w-4 h-4" /> Unsubscribe
                </button>
                <button
                  onClick={handleDelete}
                  className="flex items-center gap-1 px-4 py-2 text-sm font-bold text-red-700 bg-white border border-red-300 rounded-lg shadow hover:bg-red-100 focus:outline-none focus:ring-2 focus:ring-red-400"
                >
                  <Trash2 className="w-4 h-4" /> Delete
                </button>
              </div>
            </div>
          )}
          {/* Unsubscribe Feedback Section (clean row, margin below) */}
          {(unsubscribeResults.length > 0 || aiUnsubscribeResults.length > 0) && (
            <div className="mb-6 mt-2 border border-gray-200 rounded bg-white px-4 py-3 flex flex-col gap-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  {aiUnsubscribeResults.some(res => res.success === false) ? (
                    <AlertCircle className="w-5 h-5 text-red-500" />
                  ) : (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                  <span className={`font-medium text-sm ${aiUnsubscribeResults.some(res => res.success === false) ? 'text-red-700' : 'text-gray-900'}`}
                  >
                    {aiUnsubscribeResults.some(res => res.success === false)
                      ? `Some unsubscribes failed for ${unsubscribeCheckedCount} selected email${unsubscribeCheckedCount === 1 ? '' : 's'}`
                      : `Unsubscribe attempted for ${unsubscribeCheckedCount} selected email${unsubscribeCheckedCount === 1 ? '' : 's'}`}
                  </span>
                </div>
                <button
                  className="flex items-center gap-1 text-xs text-blue-600 hover:underline focus:outline-none ml-auto"
                  onClick={() => setUnsubscribeDropdownOpen((open) => !open)}
                  aria-expanded={unsubscribeDropdownOpen}
                >
                  {unsubscribeDropdownOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />} {unsubscribeDropdownOpen ? 'Hide Details' : 'Show Details'}
                </button>
              </div>
              {unsubscribeDropdownOpen && (
                <div className="mt-2">
                  <table className="min-w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-700 border-b">
                        <th className="py-1 pr-4">Email</th>
                        <th className="py-1 pr-4">Status</th>
                        <th className="py-1">Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {unsubscribeResults.map((result, i) => {
                        const aiResult = aiUnsubscribeResults[i] || {};
                        return (
                          <tr key={result.email_id || i} className="border-b last:border-0">
                            <td className="py-1 pr-4 text-gray-900 font-medium">
                              {result.email_id}
                            </td>
                            <td className="py-1 pr-4">
                              {aiResult.success === false ? (
                                <span className="text-red-600 font-semibold">Failed</span>
                              ) : (
                                <span className="text-green-600 font-semibold">Success</span>
                              )}
                            </td>
                            <td className="py-1 text-gray-700">
                              {aiResult.reason || aiResult.action_msg || aiResult.error || 'No details'}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}
          {/* Manage row: heading + refresh/select all */}
          <div className="flex flex-col gap-2 mb-4">
            
            <div className="flex items-center gap-4">
              <button
                onClick={loadEmails}
                className="p-2 rounded-full hover:bg-blue-100 text-blue-600"
                title="Refresh emails"
                disabled={isLoading}
              >
                <RefreshCw className={`w-5 h-5${isLoading ? ' animate-spin' : ''}`} />
              </button>
              {emails.length > 0 && (
                <button
                  onClick={handleSelectAll}
                  className="flex items-center space-x-2 text-sm text-blue-700 hover:text-blue-900 font-semibold"
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
          {/* Emails List */}
          <div className="divide-y divide-gray-200 flex-1 overflow-y-auto">
            {emails.length === 0 ? (
              <div className="px-6 py-8 text-center">
                <Mail className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-lg font-bold text-gray-900">No emails</h3>
                <p className="mt-1 text-sm text-gray-500">
                  No emails found in this category.
                </p>
              </div>
            ) : (
              emails.map((email) => (
                <div
                  key={email.id}
                  className={`my-4 px-6 py-5 rounded-xl shadow border border-gray-200 bg-white transition-all flex items-start gap-4 ${selectedEmails.has(email.id) ? 'ring-2 ring-blue-600 bg-blue-50' : 'hover:bg-gray-100 cursor-pointer'}`}
                  style={{ marginBottom: '1.5rem' }}
                >
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelectEmail(email.id);
                    }}
                    className={`mt-1 focus:outline-none ${selectedEmails.has(email.id) ? 'text-blue-600' : 'text-gray-400'}`}
                    aria-label={selectedEmails.has(email.id) ? 'Deselect email' : 'Select email'}
                  >
                    {selectedEmails.has(email.id) ? (
                      <CheckSquare className="w-5 h-4" />
                    ) : (
                      <Square className="w-5 h-4" />
                    )}
                  </button>
                  <div 
                    className="flex-1 min-w-0"
                    onClick={() => openEmailModal(email)}
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-bold text-gray-900 truncate">
                        {email.subject}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-700 mt-1 font-medium">
                      From: {email.from_email}
                    </p>
                    <p className="text-sm text-gray-500 mt-1">
                      {email.summary}
                    </p>
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