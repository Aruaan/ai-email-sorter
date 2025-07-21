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
  const [expandedResultIndexes, setExpandedResultIndexes] = useState<Set<number>>(new Set());
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
            </div>
          </div>
        </div>
      </header>

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
            <button
              onClick={() => navigate('/')}
              className="text-gray-500 hover:text-blue-600 text-sm font-medium focus:outline-none"
              style={{ minWidth: 0 }}
            >
              &larr; Back
            </button>
            <span className="text-lg font-semibold text-gray-900 truncate">{categoryName}</span>
            {categoryDescription && (
              <span className="text-xs text-gray-500 truncate">&mdash; {categoryDescription}</span>
            )}
          </div>
          {/* Bulk Actions */}
          {selectedEmails.size > 0 && (
            <div className="bg-gray-50 rounded-md p-3 mb-3 flex items-center justify-between border border-gray-200">
              <span className="text-sm text-gray-700">{selectedEmails.size} email(s) selected</span>
              <div className="flex gap-2">
                <button
                  onClick={handleUnsubscribe}
                  className="flex items-center gap-1 px-3 py-1 text-sm font-medium text-blue-600 bg-blue-50 rounded hover:bg-blue-100"
                >
                  <ExternalLink className="w-4 h-4" /> Unsubscribe
                </button>
                <button
                  onClick={handleDelete}
                  className="flex items-center gap-1 px-3 py-1 text-sm font-medium text-red-600 bg-red-50 rounded hover:bg-red-100"
                >
                  <Trash2 className="w-4 h-4" /> Delete
                </button>
              </div>
            </div>
          )}
          {/* Unsubscribe Feedback Section (collapsible, does not push content) */}
          {(unsubscribeResults.length > 0 || aiUnsubscribeResults.length > 0) && (
            <div className="mb-3 border border-gray-200 rounded bg-white px-4 pt-3 pb-2 transition-all duration-200">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="font-medium text-gray-900 text-sm">
                  Unsubscribe attempted for {unsubscribeCheckedCount} selected email{unsubscribeCheckedCount === 1 ? '' : 's'}
                </span>
                {aiUnsubscribeResults.some(res => res.success === false) && (
                  <span className="flex items-center ml-2 text-xs text-red-600" title="Some unsubscribes failed">
                    <AlertCircle className="w-4 h-4 mr-1" />
                    {aiUnsubscribeResults.filter(res => res.success === false).length} error{aiUnsubscribeResults.filter(res => res.success === false).length > 1 ? 's' : ''} occurred while unsubscribing.
                  </span>
                )}
              </div>
              <button
                className="flex items-center gap-1 mt-2 text-xs text-blue-600 hover:underline focus:outline-none"
                onClick={() => setUnsubscribeDropdownOpen((open) => !open)}
                aria-expanded={unsubscribeDropdownOpen}
              >
                {unsubscribeDropdownOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />} {unsubscribeDropdownOpen ? 'Hide Details' : 'Show Details'}
              </button>
              {unsubscribeDropdownOpen && (
                <div className="mt-2">
                  {unsubscribeResults.length > 0 && (
                    <div className="mb-2 border border-gray-100 rounded bg-white px-3 py-2">
                      {unsubscribeResults.map((result, index) => (
                        <div key={index} className="text-xs text-green-700 mb-1 leading-tight">
                          {result.unsubscribe_links.length > 0 ? (
                            <span>Email {result.email_id}: {result.unsubscribe_links.length} unsubscribe link(s) found</span>
                          ) : (
                            <span>Email {result.email_id}: No unsubscribe links found</span>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  {aiUnsubscribeResults.length > 0 && (
                    <div className="w-full mt-2">
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                        <h3 className="text-xs font-medium text-blue-800 mb-2">AI Unsubscribe Actions</h3>
                        <div className="overflow-x-auto">
                          <table className="min-w-full text-xs border">
                            <thead>
                              <tr className="bg-blue-100">
                                <th className="px-2 py-1 border">Index</th>
                                <th className="px-2 py-1 border">Unsubscribe Link</th>
                                <th className="px-2 py-1 border">Status</th>
                                <th className="px-2 py-1 border">Error</th>
                                <th className="px-2 py-1 border">View</th>
                              </tr>
                            </thead>
                            <tbody>
                              {aiUnsubscribeResults.map((res, idx) => (
                                <tr key={idx} className="border-b">
                                  <td className="px-2 py-1 border align-top">{idx + 1}</td>
                                  <td className="px-2 py-1 border align-top break-all max-w-xs">
                                    <a href={res.link} target="_blank" rel="noopener noreferrer" className="text-blue-600 underline">{res.link}</a>
                                  </td>
                                  <td className="px-2 py-1 border align-top">
                                    {res.success ? (
                                      <span className="text-green-700 font-bold">Yes</span>
                                    ) : (
                                      <span className="text-red-700 font-bold">No</span>
                                    )}
                                  </td>
                                  <td className="px-2 py-1 border align-top">{res.reason}</td>
                                  <td className="px-2 py-1 border align-top">
                                    <button
                                      className="text-blue-600 underline text-xs"
                                      onClick={() => {
                                        const newSet = new Set(expandedResultIndexes);
                                        if (newSet.has(idx)) newSet.delete(idx); else newSet.add(idx);
                                        setExpandedResultIndexes(newSet);
                                      }}
                                    >
                                      {expandedResultIndexes.has(idx) ? 'Hide' : 'View'}
                                    </button>
                                    {expandedResultIndexes.has(idx) && (
                                      <div className="mt-2 bg-white border rounded p-2 max-w-lg overflow-x-auto">
                                        <div className="mb-1"><span className="font-semibold">AI Actions:</span><br /><pre className="whitespace-pre-wrap text-xs">{res.actions || '(none)'}</pre></div>
                                        <div className="mb-1"><span className="font-semibold">Action Success:</span> {res.action_success ? 'Yes' : 'No'}</div>
                                        <div className="mb-1"><span className="font-semibold">Action Message:</span> {res.action_msg}</div>
                                        <div><span className="font-semibold">Log:</span><br /><pre className="whitespace-pre-wrap text-xs">{Array.isArray(res.log) ? res.log.join('\n') : res.log}</pre></div>
                                      </div>
                                    )}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          {/* Emails List */}
          <div className="flex-1 flex flex-col mt-2">
            <div className="flex items-center justify-between mb-2">
              <h2 className="text-base font-medium text-gray-900">Emails</h2>
              <div className="flex items-center gap-2">
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
            <div className="divide-y divide-gray-200 flex-1 overflow-y-auto">
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
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectEmail(email.id);
                        }}
                        className="mt-1"
                      >
                        {selectedEmails.has(email.id) ? (
                          <CheckSquare className="w-4 h-4 text-blue-600" />
                        ) : (
                          <Square className="w-4 h-4 text-gray-400" />
                        )}
                      </button>
                      <div 
                        className="flex-1 min-w-0 cursor-pointer"
                        onClick={() => openEmailModal(email)}
                      >
                        <div className="flex items-center justify-between">
                          <h3 className="text-sm font-medium text-gray-900 truncate">
                            {email.subject}
                          </h3>
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