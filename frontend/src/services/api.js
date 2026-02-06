import axios from 'axios'

// Create axios instance with default configuration
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor to add auth token to all requests
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor to handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // If we get a 401, clear the token and redirect to login
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth API
export const authAPI = {
  login: async (email, password) => {
    // OAuth2 expects form data, not JSON
    const formData = new URLSearchParams()
    formData.append('username', email)
    formData.append('password', password)
    const response = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return response.data
  },

  register: async (email, password) => {
    const response = await api.post('/auth/register', { email, password })
    return response.data
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

// Accounts API
export const accountsAPI = {
  list: async () => {
    const response = await api.get('/accounts/')
    return response.data
  },

  create: async (data) => {
    const response = await api.post('/accounts/', data)
    return response.data
  },

  get: async (id) => {
    const response = await api.get(`/accounts/${id}`)
    return response.data
  },

  update: async (id, data) => {
    const response = await api.put(`/accounts/${id}`, data)
    return response.data
  },

  delete: async (id) => {
    await api.delete(`/accounts/${id}`)
  },
}

// Transactions API
export const transactionsAPI = {
  list: async (params = {}) => {
    const response = await api.get('/transactions/', { params })
    return response.data
  },

  create: async (data) => {
    const response = await api.post('/transactions/', data)
    return response.data
  },

  get: async (id) => {
    const response = await api.get(`/transactions/${id}`)
    return response.data
  },

  update: async (id, data) => {
    const response = await api.put(`/transactions/${id}`, data)
    return response.data
  },

  delete: async (id) => {
    await api.delete(`/transactions/${id}`)
  },

  bulkCategorize: async (transactionIds, categoryId) => {
    const response = await api.post('/transactions/bulk-categorize', {
      transaction_ids: transactionIds,
      category_id: categoryId,
    })
    return response.data
  },
}

// Categories API
export const categoriesAPI = {
  list: async () => {
    const response = await api.get('/categories/')
    return response.data
  },

  create: async (data) => {
    const response = await api.post('/categories/', data)
    return response.data
  },

  update: async (id, data) => {
    const response = await api.put(`/categories/${id}`, data)
    return response.data
  },

  delete: async (id) => {
    await api.delete(`/categories/${id}`)
  },

  // Category rules
  listRules: async () => {
    const response = await api.get('/categories/rules/')
    return response.data
  },

  createRule: async (data) => {
    const response = await api.post('/categories/rules/', data)
    return response.data
  },

  deleteRule: async (id) => {
    await api.delete(`/categories/rules/${id}`)
  },
}

// Dashboard API
export const dashboardAPI = {
  getSummary: async (months = 1) => {
    const response = await api.get('/dashboard/summary', { params: { months } })
    return response.data
  },

  getSpendingByCategory: async (months = 1) => {
    const response = await api.get('/dashboard/spending-by-category', { params: { months } })
    return response.data
  },

  getMonthlyTrend: async (months = 6) => {
    const response = await api.get('/dashboard/monthly-trend', { params: { months } })
    return response.data
  },

  getRecentTransactions: async (limit = 10) => {
    const response = await api.get('/dashboard/recent-transactions', { params: { limit } })
    return response.data
  },
}

// Import API
export const importAPI = {
  importCSV: async (file, accountId) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('account_id', accountId)
    const response = await api.post('/import/csv', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  importOFX: async (file, accountId) => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('account_id', accountId)
    const response = await api.post('/import/ofx', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return response.data
  },

  getFormats: async () => {
    const response = await api.get('/import/formats')
    return response.data
  },
}

export default api
