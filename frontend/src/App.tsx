import React, { useState, useEffect } from 'react';
import { Routes, Route, Navigate, useSearchParams, useLocation, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import CategoryView from './pages/CategoryView';
import { authAPI } from './services/api';
import { SessionInfo } from './types';
import { AccountProvider } from './contexts/AccountContext';

// Callback handler component
const CallbackHandler: React.FC<{ onLogin: (email: string, sessionId: string) => void }> = ({ onLogin }) => {
  const [searchParams] = useSearchParams();
  const [hasProcessed, setHasProcessed] = useState(false);
  const processingRef = React.useRef(false);
  const email = searchParams.get('email');
  const sessionId = searchParams.get('session_id');
  const accountAdded = searchParams.get('account_added');

  useEffect(() => {
    if (hasProcessed || processingRef.current) return; // Prevent multiple processing
    
    processingRef.current = true;
    console.log('CallbackHandler - URL params:', { email, sessionId, accountAdded });
    
    // Handle account added notification first
    if (accountAdded && sessionId) {
      // No alert, just redirect to dashboard
      setHasProcessed(true);
      window.location.href = '/';
      return;
    }
    
    // Handle regular login
    if (email && sessionId) {
      console.log('Calling onLogin with:', { email, sessionId });
      setHasProcessed(true);
      onLogin(email, sessionId);
      // Navigate to dashboard after login
      window.location.href = '/';
      return;
    }
    
    // No valid parameters found
    console.log('No valid parameters found, redirecting to login');
    setHasProcessed(true);
    window.location.href = '/login';
  }, [email, sessionId, accountAdded, onLogin, hasProcessed]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="text-lg mb-4">Completing sign in...</div>
        <div className="text-sm text-gray-600">
          Email: {email || 'Not found'}<br/>
          Session ID: {sessionId || 'Not found'}<br/>
          Account Added: {accountAdded || 'None'}
        </div>
      </div>
    </div>
  );
};

function App() {
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sessionInfo, setSessionInfo] = useState<SessionInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [toastTimeout, setToastTimeout] = useState<number | null>(null);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    // Check for stored session info on app start
    const storedEmail = localStorage.getItem('userEmail');
    const storedSessionId = localStorage.getItem('sessionId');
    
    if (storedEmail && storedSessionId) {
      setUserEmail(storedEmail);
      setSessionId(storedSessionId);
      
      // Load session info
      authAPI.getSessionInfo(storedSessionId)
        .then(setSessionInfo)
        .catch(() => {
          // Session invalid, clear storage
          localStorage.removeItem('userEmail');
          localStorage.removeItem('sessionId');
          setUserEmail(null);
          setSessionId(null);
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Check for account_cancelled param
    const params = new URLSearchParams(location.search);
    if (params.get('account_cancelled')) {
      setToastMessage('Account addition cancelled.');
      if (toastTimeout) clearTimeout(toastTimeout);
      const timeout = window.setTimeout(() => setToastMessage(null), 4000);
      setToastTimeout(timeout);
      // Remove the param from the URL
      params.delete('account_cancelled');
      navigate({ pathname: location.pathname, search: params.toString() }, { replace: true });
    }
  }, [location.search]);

  const handleLogin = (email: string, sessionId: string) => {
    setUserEmail(email);
    setSessionId(sessionId);
    localStorage.setItem('userEmail', email);
    localStorage.setItem('sessionId', sessionId);
    
    // Set the logged-in account as the active account
    localStorage.setItem('activeAccount', email);
    
    // Load session info
    authAPI.getSessionInfo(sessionId)
      .then(setSessionInfo)
      .catch(console.error);
  };

  const handleLogout = () => {
    // Call backend logout endpoint if we have a session
    if (sessionId) {
      fetch(`/api/auth/logout?session_id=${sessionId}`, { method: 'POST' })
        .catch(console.error); // Don't block logout if this fails
    }
    
    setUserEmail(null);
    setSessionId(null);
    setSessionInfo(null);
    // Clear all session-related data from localStorage
    localStorage.removeItem('userEmail');
    localStorage.removeItem('sessionId');
    localStorage.removeItem('activeAccount');
  };

  if (isLoading) {
    return <div className="flex items-center justify-center min-h-screen">Loading...</div>;
  }

  return (
    <AccountProvider key={sessionId || 'no-session'} initialActiveAccount={sessionInfo?.primary_account || userEmail || ''}>
      <div className="App">
        {toastMessage && (
          <div className="fixed top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-6 py-3 rounded shadow-lg z-50 transition-all">
            {toastMessage}
          </div>
        )}
        <Routes>
          <Route 
            path="/login" 
            element={
              userEmail ? <Navigate to="/" replace /> : <Login onLogin={handleLogin} />
            } 
          />
          <Route 
            path="/callback" 
            element={<CallbackHandler onLogin={handleLogin} />} 
          />
          <Route 
            path="/dashboard" 
            element={<CallbackHandler onLogin={handleLogin} />} 
          />
          <Route 
            path="/" 
            element={
              userEmail && sessionId ? (
                <Dashboard 
                  userEmail={userEmail} 
                  sessionId={sessionId}
                  sessionInfo={sessionInfo}
                  onLogout={handleLogout}
                  onSessionUpdate={setSessionInfo}
                />
              ) : (
                <Navigate to="/login" replace />
              )
            } 
          />
          <Route 
            path="/category/:categoryId" 
            element={
              userEmail && sessionId ? (
                <CategoryView 
                  userEmail={userEmail} 
                  sessionId={sessionId}
                  sessionInfo={sessionInfo}
                />
              ) : (
                <Navigate to="/login" replace />
              )
            } 
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </AccountProvider>
  );
}

export default App;
