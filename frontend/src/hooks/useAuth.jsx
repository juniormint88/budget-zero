import { useState, useEffect, useCallback, createContext, useContext } from 'react'
import { useNavigate } from 'react-router-dom'
import { authAPI } from '../services/api'

// Create auth context
const AuthContext = createContext(null)

/**
 * Auth provider component that wraps the app and provides authentication state.
 */
export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const navigate = useNavigate()

  // Check if user is authenticated on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('token')
      if (!token) {
        setIsLoading(false)
        return
      }

      try {
        const userData = await authAPI.getCurrentUser()
        setUser(userData)
      } catch (error) {
        // Token is invalid, clear it
        localStorage.removeItem('token')
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  // Login function
  const login = useCallback(async (email, password) => {
    const response = await authAPI.login(email, password)
    localStorage.setItem('token', response.access_token)

    // Fetch user data after login
    const userData = await authAPI.getCurrentUser()
    setUser(userData)

    navigate('/')
    return userData
  }, [navigate])

  // Register function
  const register = useCallback(async (email, password) => {
    await authAPI.register(email, password)
    // Auto-login after registration
    return login(email, password)
  }, [login])

  // Logout function
  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setUser(null)
    navigate('/login')
  }, [navigate])

  const value = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    register,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

/**
 * Hook to access authentication state and functions.
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
