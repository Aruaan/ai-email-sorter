import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { categoriesAPI, authAPI, emailsAPI } from '../services/api';
import { Category, SessionInfo } from '../types';
import { ChevronDown, Plus, Mail, Settings, LogOut, UserPlus } from 'lucide-react';
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
  const [isProcessingEmails, setIsProcessingEmails] = useState(false);
  const [showAccountDropdown, setShowAccountDropdown] = useState(false);
  const { activeAccount, setActiveAccount } = useAccount();
  const navigate = useNavigate();

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
      const data = await categoriesAPI.getCategories(userEmail);
      setCategories(data);
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
        userEmail
      );
      setCategories([...categories, newCategory]);
      setNewCategoryName('');
      setNewCategoryDescription('');
      setShowAddForm(false);
    } catch (error) {
      console.error('Failed to create category:', error);
    }
  };

  const handleProcessEmails = async () => {
    setIsProcessingEmails(true);
    try {
      // Use selected account or primary account, not userEmail
      const accountToProcess = activeAccount || sessionInfo?.primary_account || userEmail;
      console.log('Processing emails for account:', accountToProcess);
      console.log('Session ID:', sessionId);
      
      const result = await emailsAPI.processEmails(sessionId, accountToProcess, 3);
      console.log('API result:', result);
      
      // Check if result is an error object
      if (result && result.error) {
        console.error('API returned error:', result.error);
        alert(`Error: ${result.error}`);
        return;
      }
      
      // Check if result is an array
      if (Array.isArray(result)) {
        console.log('Success! Processed emails:', result.length);
        alert(`Processed ${result.length} emails successfully for ${accountToProcess}!`);
        // Refresh categories to show updated email counts
        loadCategories();
      } else {
        console.error('Unexpected result format:', result);
        alert('Unexpected response format from server');
      }
    } catch (error) {
      console.error('Failed to process emails:', error);
      alert('Failed to process emails. Please try again.');
    } finally {
      setIsProcessingEmails(false);
    }
  };

  const handleAddAccount = () => {
    authAPI.addAccount(sessionId);
  };

  const handleSetPrimaryAccount = async (email: string) => {
    try {
      await authAPI.setPrimaryAccount(sessionId, email);
      // Update global active account
      setActiveAccount(email);
      // Refresh session info
      const updatedSessionInfo = await authAPI.getSessionInfo(sessionId);
      onSessionUpdate(updatedSessionInfo);
      setShowAccountDropdown(false);
    } catch (error) {
      console.error('Failed to set primary account:', error);
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

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-lg">Loading categories...</div>
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
                          {account.email === activeAccount ? (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                              Active
                            </span>
                          ) : (
                            <button
                              onClick={() => handleSetPrimaryAccount(account.email)}
                              className="text-xs text-blue-600 hover:text-blue-800"
                            >
                              Switch
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
              <span className="text-sm text-gray-700">
                {activeAccount || sessionInfo?.primary_account || userEmail}
              </span>
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
        {/* Email Processing Section */}
        <div className="bg-white shadow rounded-lg p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-medium text-gray-900">Email Processing</h2>
              <p className="text-sm text-gray-600">
                Process and categorize your emails using AI
              </p>
            </div>
            <div className="flex items-center space-x-4">
              {/* Simple Account Selection */}
              {sessionInfo && sessionInfo.accounts.length > 1 && (
                <div className="flex items-center space-x-2">
                  {sessionInfo.accounts.map((account) => (
                    <button
                      key={account.email}
                      onClick={() => setActiveAccount(
                        activeAccount === account.email ? '' : account.email
                      )}
                      className={`px-3 py-1 text-sm rounded-full border transition-colors ${
                        (activeAccount === account.email) || 
                        (!activeAccount && account.email === sessionInfo.primary_account)
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {account.email.split('@')[0]}
                    </button>
                  ))}
                </div>
              )}
              <button
                onClick={handleProcessEmails}
                disabled={isProcessingEmails}
                className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Mail className="w-4 h-4" />
                <span>{isProcessingEmails ? 'Processing...' : 'Process Emails'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Categories Section */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-medium text-gray-900">Categories</h2>
              <button
                onClick={() => setShowAddForm(!showAddForm)}
                className="flex items-center space-x-2 px-3 py-2 text-sm font-medium text-blue-600 bg-blue-50 rounded-md hover:bg-blue-100"
              >
                <Plus className="w-4 h-4" />
                <span>Add Category</span>
              </button>
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
            {categories.length === 0 ? (
              <div className="text-center py-8">
                <Mail className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-sm font-medium text-gray-900">No categories</h3>
                <p className="mt-1 text-sm text-gray-500">
                  Get started by creating your first category.
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {categories.map((category) => (
                  <div
                    key={category.id}
                    onClick={() => navigate(`/category/${category.id}`)}
                    className="bg-gray-50 rounded-lg p-4 cursor-pointer hover:bg-gray-100 transition-colors"
                  >
                    <h3 className="text-lg font-medium text-gray-900">{category.name}</h3>
                    {category.description && (
                      <p className="mt-1 text-sm text-gray-600">{category.description}</p>
                    )}
                    <div className="mt-2 flex items-center text-sm text-gray-500">
                      <Mail className="w-4 h-4 mr-1" />
                      <span>View emails</span>
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