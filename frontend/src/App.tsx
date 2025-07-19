import { Routes, Route, Navigate, useSearchParams } from 'react-router-dom'
import { useState, useEffect } from 'react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import CategoryView from './pages/CategoryView'

function CallbackHandler({ onLogin }: { onLogin: (email: string) => void }) {
  const [searchParams] = useSearchParams()
  
  useEffect(() => {
    const email = searchParams.get('email')
    
    if (email) {
      onLogin(email)
    } else {
      // Fallback: redirect to login if no email
      window.location.href = '/login'
    }
  }, [searchParams, onLogin])

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-lg">Completing sign in...</div>
    </div>
  )
}

function App() {
  const [userEmail, setUserEmail] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check if user is logged in on app start
    const storedEmail = localStorage.getItem('userEmail')
    if (storedEmail) {
      setUserEmail(storedEmail)
    }
    setIsLoading(false)
  }, [])

  const handleLogin = (email: string) => {
    setUserEmail(email)
    localStorage.setItem('userEmail', email)
  }

  const handleLogout = () => {
    setUserEmail(null)
    localStorage.removeItem('userEmail')
  }

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
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
          path="/" 
          element={
            userEmail ? <Dashboard userEmail={userEmail} onLogout={handleLogout} /> : <Navigate to="/login" replace />
          } 
        />
        <Route 
          path="/category/:categoryId" 
          element={
            userEmail ? <CategoryView userEmail={userEmail} onLogout={handleLogout} /> : <Navigate to="/login" replace />
          } 
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  )
}

export default App
