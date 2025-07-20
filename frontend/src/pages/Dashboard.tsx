import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { categoriesAPI, authAPI, emailsAPI } from '../services/api';
import { Category, SessionInfo } from '../types';
import { ChevronDown, Plus, Mail, LogOut, UserPlus, RefreshCw } from 'lucide-react';
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
  const [emailCounts, setEmailCounts] = useState<Record<number, number>>({});
  const [newEmailCategories, setNewEmailCategories] = useState<number[]>([]); // Track categories with new emails
  // Add account filter state
  const [accountFilter, setAccountFilter] = useState('All Accounts');
  // Add a local isRefreshing state
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    loadCategories();
    // Refresh session info to get latest account data
    if (sessionId) {
      refreshSessionInfo();
    }
  }, [userEmail, sessionId]);

  // Update active account when sessionInfo changes (e.g., new account added)
  useEffect(() => {
    if (sessionInfo?.primary_account && !activeAccount) {
      setActiveAccount(sessionInfo.primary_account);
    }
  }, [sessionInfo, activeAccount, setActiveAccount]);

  const loadCategories = async () => {
    try {
      const data = await categoriesAPI.getCategories(sessionId);
      setCategories(data);
      // Fetch email counts for each category
      const counts: Record<number, number> = {};
      for (const cat of data) {
        const emails = await emailsAPI.getEmails(sessionId, cat.id);
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

  const handleAddAccount = () => {
    authAPI.addAccount(sessionId);
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading categories...</div>
      </div>
    );
  }

  // Sort categories by email count (desc) and filter by account
  const sortedCategories = [...categories].sort(
    (a, b) => (emailCounts[b.id] ?? 0) - (emailCounts[a.id] ?? 0)
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
              <div className="relative">
                <button
                  onClick={() => setShowAccountDropdown(!showAccountDropdown)}
                  className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <UserPlus className="w-4 h-4" />
                  <span>{sessionInfo?.accounts.length || 0} Accounts</span>
                  <ChevronDown className="w-4 h-4" />
                </button>
                
                {showAccountDropdown && (
                  <div className="absolute right-0 mt-2 w-64 bg-white rounded-md shadow-lg border border-gray-200 z-10">
                    <div className="py-2">
                      <div className="px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                        Accounts
                      </div>
                      {sessionInfo?.accounts.map((account) => (
                        <div key={account.email} className="flex items-center justify-between px-4 py-2 hover:bg-gray-50">
                          <span className="text-sm text-gray-700">{account.email}</span>
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
                <span>Logout</span>
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
              <select
                value={accountFilter}
                onChange={e => setAccountFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="All Accounts">All Accounts</option>
                {sessionInfo?.accounts.map(acc => (
                  <option key={acc.email} value={acc.email}>{acc.email}</option>
                ))}
              </select>
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
                    onClick={() => {
                      navigate(`/category/${category.id}`);
                      setNewEmailCategories(newEmailCategories.filter(id => id !== category.id));
                    }}
                    className="bg-gray-50 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition-colors relative"
                  >
                    <h3 className="text-lg font-medium text-gray-900 flex items-center justify-between">
                      {category.name}
                      <span className="ml-2 inline-flex items-center justify-center min-w-[2.5rem] h-8 px-3 py-1 rounded-full text-sm font-bold bg-blue-600 text-white shadow">
                        {emailCounts[category.id] ?? 0}
                      </span>
                      {/* Mail icon with pulse for new emails */}
                      {newEmailCategories.includes(category.id) && (
                        <span className="absolute top-2 right-2">
                          <Mail className="w-5 h-5 text-blue-500 animate-pulse" />
                        </span>
                      )}
                    </h3>
                    {category.description && (
                      <p
                        className="mt-1 text-sm text-gray-600 truncate"
                        title={category.description}
                        style={{ maxWidth: '100%', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}
                      >
                        {category.description}
                      </p>
                    )}
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