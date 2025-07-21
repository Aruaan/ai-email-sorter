import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { categoriesAPI, authAPI, emailsAPI, sessionAPI } from '../services/api';
import { Category, SessionInfo } from '../types';
import { ChevronDown, Plus, Mail, LogOut, UserPlus, RefreshCw, X } from 'lucide-react';
import { useAccount } from '../contexts/AccountContext';

interface DashboardProps {
  userEmail: string;
  sessionId: string;
  sessionInfo: SessionInfo | null;
  onLogout: () => void;
  onSessionUpdate: (sessionInfo: SessionInfo) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ 
  userEmail, 
  sessionId, 
  sessionInfo, 
  onLogout, 
  onSessionUpdate 
}) => {
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [newCategoryDescription, setNewCategoryDescription] = useState('');
  const [showAccountDropdown, setShowAccountDropdown] = useState(false);
  const { activeAccount, setActiveAccount } = useAccount();
  const navigate = useNavigate();
  const [emailCounts, setEmailCounts] = useState<Record<string, number>>({});
  const [newEmailCategories, setNewEmailCategories] = useState<string[]>([]); // Track categories with new emails
  // Add account filter state - this will be the display value for the dropdown
  const [accountFilter, setAccountFilter] = useState(activeAccount || 'All Accounts');
  // Add a local isRefreshing state
  const [isRefreshing, setIsRefreshing] = useState(false);
  // Add state for account removal
  const [removingAccount, setRemovingAccount] = useState<string | null>(null);
  // Add ref for the dropdown button
  const dropdownButtonRef = useRef<HTMLButtonElement>(null);
  // Remove all edit-related state and handlers
  // Remove handleEditCategory, handleSaveCategoryEdit, handleCancelEdit, editingCategory, editCategoryName, editCategoryDescription
  // Remove edit button and edit form in the category list


  useEffect(() => {
    loadCategories();
    // Refresh session info to get latest account data
    if (sessionId) {
      refreshSessionInfo();
    }
  }, [userEmail, sessionId]);

  // Reload categories when active account changes
  useEffect(() => {
    if (!isLoading) {
      loadCategories();
    }
  }, [activeAccount]);

  // Handle Escape key to close account dropdown
  useEffect(() => {
    const handleEscapeKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && showAccountDropdown) {
        setShowAccountDropdown(false);
      }
    };

    if (showAccountDropdown) {
      document.addEventListener('keydown', handleEscapeKey);
    }

    return () => {
      document.removeEventListener('keydown', handleEscapeKey);
    };
  }, [showAccountDropdown]);

  // Handle click outside to close account dropdown
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;
      const dropdownContainer = target.closest('.account-dropdown-container');
      
      if (showAccountDropdown && !dropdownContainer && target !== dropdownButtonRef.current) {
        setShowAccountDropdown(false);
      }
    };

    if (showAccountDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showAccountDropdown]);

  // Update active account when sessionInfo changes (e.g., new account added)
  useEffect(() => {
    if (sessionInfo?.accounts) {
      if (sessionInfo.accounts.length === 1) {
        // If there's only one account, automatically set it as active
        setActiveAccount(sessionInfo.accounts[0].email);
      } else if (sessionInfo.primary_account && !activeAccount) {
        // If there are multiple accounts and no active account is set, use primary
        setActiveAccount(sessionInfo.primary_account);
      } else if (sessionInfo.accounts.length > 1 && !activeAccount) {
        // If multiple accounts but no active account, default to "All Accounts"
        setActiveAccount('All Accounts');
      }
    }
  }, [sessionInfo, activeAccount, setActiveAccount]);

  // Sync accountFilter with activeAccount
  useEffect(() => {
    setAccountFilter(activeAccount);
  }, [activeAccount]);

  // Remove the problematic sync useEffect that was causing the revert
  // The accountFilter and activeAccount will be managed separately

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.getCategories(sessionId);
      setCategories(data);
      // Fetch email counts for each category based on active account
      const counts: Record<string, number> = {};
      for (const cat of data) {
        // If there's only one account or "All Accounts" is selected, don't filter by user_email
        // Otherwise, use the selected account
        const userEmail = (sessionInfo?.accounts.length === 1 || activeAccount === 'All Accounts') ? undefined : activeAccount;
        const emails = await emailsAPI.getEmails(sessionId, cat.id, userEmail);
        counts[cat.id] = emails.length;
      }
      setEmailCounts(counts);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCategoryName.trim()) return;

    try {
      const newCategory = await categoriesAPI.createCategory(
        newCategoryName,
        newCategoryDescription,
        sessionId
      );
      setCategories([...categories, newCategory]);
      setNewCategoryName('');
      setNewCategoryDescription('');
      setShowAddForm(false);
    } catch (error) {
      console.error('Failed to create category:', error);
    }
  };

  const BASE_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : 'https://ai-email-sorter-1-1jhi.onrender.com';
  const handleAddAccount = () => {
    window.location.assign(`${BASE_URL}/auth/google/add-account?session_id=${sessionId}`);
  };

  const handleRemoveAccount = async (email: string) => {
    if (!sessionInfo || sessionInfo.accounts.length <= 1) {
      alert('Cannot remove the last account. Please add another account first.');
      return;
    }

    if (!confirm(`Are you sure you want to remove ${email} from this session?`)) {
      return;
    }

    try {
      setRemovingAccount(email);
      await sessionAPI.removeAccount(sessionId, email);
      
      // Refresh session info to get updated account list
      await refreshSessionInfo();
      
      // If the removed account was the current filter, reset to "All Accounts"
      if (accountFilter === email) {
        setAccountFilter('All Accounts');
      }
      
      // If the removed account was the active account, clear it
      if (activeAccount === email) {
        setActiveAccount('');
      }
      
      // Close the dropdown after successful removal
      setShowAccountDropdown(false);
      
      console.log(`Successfully removed account: ${email}`);
    } catch (error) {
      console.error('Failed to remove account:', error);
      alert('Failed to remove account. Please try again.');
    } finally {
      setRemovingAccount(null);
    }
  };


  const refreshSessionInfo = async () => {
    try {
      const updatedSessionInfo = await authAPI.getSessionInfo(sessionId);
      onSessionUpdate(updatedSessionInfo);
    } catch (error) {
      console.error('Failed to refresh session info:', error);
    }
  };

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await loadCategories();
    setTimeout(() => setIsRefreshing(false), 500); // short delay for feedback
  };

  // Remove all edit-related state and handlers
  // Remove handleEditCategory, handleSaveCategoryEdit, handleCancelEdit, editingCategory, editCategoryName, editCategoryDescription
  // Remove edit button and edit form in the category list
  // Only display category name and description

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading categories...</div>
      </div>
    );
  }

  // Sort categories by name to maintain consistent order
  const sortedCategories = [...categories].sort(
    (a, b) => a.name.localeCompare(b.name)
  );
  

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">AI Email Sorter</h1>
              
              {/* Account Switcher */}
              <div className="relative account-dropdown-container">
                <button
                  ref={dropdownButtonRef}
                  onClick={() => setShowAccountDropdown(!showAccountDropdown)}
                  className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>{sessionInfo?.accounts.length || 0} Accounts</span>
                  <ChevronDown className={`w-4 h-4 transition-transform duration-200 ${showAccountDropdown ? 'rotate-180' : ''}`} />
                </button>
                
                {showAccountDropdown && (
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                    <div className="py-2">
                      <div className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Accounts
                      </div>
                      {sessionInfo?.accounts.map((account) => (
                        <div key={account.email} className="flex items-center justify-between px-4 py-2 hover:bg-gray-50">
                          <span className="text-sm text-gray-700 truncate flex-1">{account.email}</span>
                          {sessionInfo.accounts.length > 1 && (
                            <button
                              onClick={() => handleRemoveAccount(account.email)}
                              disabled={removingAccount === account.email}
                              className="ml-2 p-1 text-red-500 hover:text-red-700 hover:bg-red-50 rounded disabled:opacity-50"
                              title={`Remove ${account.email}`}
                            >
                              {removingAccount === account.email ? (
                                <div className="w-4 h-4 border-2 border-red-500 border-t-transparent rounded-full animate-spin"></div>
                              ) : (
                                <X className="w-4 h-4" />
                              )}
                            </button>
                          )}
                        </div>
                      ))}
                      <div className="border-t border-gray-200 mt-2 pt-2">
                        <button
                          onClick={handleAddAccount}
                          className="w-full text-left px-4 py-2 text-sm text-blue-600 hover:bg-blue-50 flex items-center space-x-2"
                        >
                          <Plus className="w-4 h-4" />
                          <span>Add Account</span>
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={onLogout}
                className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                <LogOut className="w-4 h-4" />
                <span>{(sessionInfo?.accounts.length || 0) > 1 ? 'Logout All' : 'Logout'}</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Categories Section */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between mb-4">
              {/* Only show account dropdown when there are multiple accounts */}
              {sessionInfo && sessionInfo.accounts.length > 1 ? (
                <select
                  value={activeAccount}
                  onChange={e => {
                    const newFilter = e.target.value;
                    console.log('Account filter changed:', { from: activeAccount, to: newFilter });
                    
                    // Update both accountFilter and activeAccount
                    setAccountFilter(newFilter);
                    setActiveAccount(newFilter);
                  }}
                  className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="All Accounts">All Accounts</option>
                  {sessionInfo.accounts.map(acc => (
                    <option key={acc.email} value={acc.email}>{acc.email}</option>
                  ))}
                </select>
              ) : (
                <div className="text-sm text-gray-600">
                  {sessionInfo?.accounts.length === 1 
                    ? `Account: ${sessionInfo.accounts[0].email}`
                    : 'No accounts available'
                  }
                </div>
              )}
              <div className="flex items-center space-x-2">
                <button
                  onClick={handleRefresh}
                  className="p-2 rounded-full hover:bg-blue-100 text-blue-600"
                  title="Refresh categories and emails"
                  disabled={isRefreshing}
                >
                  <RefreshCw className={`w-5 h-5 ${isRefreshing ? 'animate-spin' : ''}`} />
                </button>
                <button
                  onClick={() => setShowAddForm(!showAddForm)}
                  className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add Category</span>
                </button>
              </div>
            </div>
          </div>

          {/* Add Category Form */}
          {showAddForm && (
            <div className="px-6 py-4 border-b border-gray-200">
              <form onSubmit={handleCreateCategory} className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700">
                    Category Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={newCategoryName}
                    onChange={(e) => setNewCategoryName(e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="e.g., Work, Personal, Newsletters"
                    required
                  />
                </div>
                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700">
                    Description
                  </label>
                  <textarea
                    id="description"
                    value={newCategoryDescription}
                    onChange={(e) => setNewCategoryDescription(e.target.value)}
                    className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Describe what emails belong in this category"
                    rows={3}
                  />
                </div>
                <div className="flex space-x-3">
                  <button
                    type="submit"
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Create Category
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddForm(false)}
                    className="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Categories List */}
          <div className="p-6">
            {sortedCategories.length === 0 ? (
              <div className="text-center py-8">
                <Mail className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No categories</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating your first category.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {sortedCategories.map((category) => (
                  <div
                    key={category.id}
                    className="bg-gray-50 rounded-lg p-4 hover:bg-gray-100 transition-colors relative"
                  >
                    {/* View mode */}
                    <div
                      onClick={() => {
                        navigate(`/category/${category.id}`);
                        setNewEmailCategories(newEmailCategories.filter(id => id !== category.id));
                      }}
                      className="cursor-pointer"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-lg font-medium text-gray-900 flex items-center">
                          {category.name}
                        </h3>
                        <span className="inline-flex items-center justify-center min-w-[2.5rem] h-8 px-3 py-1 rounded-full text-sm font-bold bg-blue-600 text-white shadow">
                          {emailCounts[category.id] ?? 0}
                        </span>
                      </div>
                      {/* Mail icon with pulse for new emails */}
                      {newEmailCategories.includes(category.id) && (
                        <span className="absolute top-2 right-2">
                          <Mail className="w-5 h-5 text-blue-500 animate-pulse" />
                        </span>
                      )}
                      {category.description && (
                        <p
                          className="text-sm text-gray-600 truncate"
                          title={category.description}
                          style={{ maxWidth: '100%', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
                        >
                          {category.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    
    </div>
  );
};

export default Dashboard; 