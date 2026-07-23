import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          })
          const { access_token, refresh_token: newRefresh } = response.data
          localStorage.setItem('access_token', access_token)
          localStorage.setItem('refresh_token', newRefresh)
          originalRequest.headers.Authorization = `Bearer ${access_token}`
          return api(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }
    return Promise.reject(error)
  }
)

export default api

export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  refresh: (data) => api.post('/auth/refresh', data),
  getMe: () => api.get('/auth/me'),
  updateMe: (data) => api.put('/auth/me', data),
  changePassword: (data) => api.post('/auth/change-password', data),
  forgotPassword: (data) => api.post('/auth/forgot-password', data),
  resetPassword: (data) => api.post('/auth/reset-password', data),
}

export const jobsAPI = {
  list: (params) => api.get('/jobs/', { params }),
  get: (id) => api.get(`/jobs/${id}`),
  create: (data) => api.post('/jobs/', data),
  update: (id, data) => api.put(`/jobs/${id}`, data),
  delete: (id) => api.delete(`/jobs/${id}`),
  getCandidates: (id) => api.get(`/jobs/${id}/candidates`),
}

export const candidatesAPI = {
  list: (params) => api.get('/candidates/', { params }),
  get: (id) => api.get(`/candidates/${id}`),
  update: (id, params) => api.put(`/candidates/${id}`, null, { params }),
  delete: (id) => api.delete(`/candidates/${id}`),
  upload: (formData) => api.post('/candidates/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  uploadMultiple: (formData) => api.post('/candidates/upload-multiple', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  parse: (id) => api.post(`/candidates/${id}/parse`),
  analyze: (id, jobId) => api.post(`/candidates/${id}/analyze`, null, {
    params: jobId ? { job_id: jobId } : {},
  }),
  parseAndAnalyze: (id, jobId) => api.post(`/candidates/${id}/parse-and-analyze`, null, {
    params: jobId ? { job_id: jobId } : {},
  }),
}

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getSkillAnalytics: () => api.get('/dashboard/analytics/skills'),
  getRankAnalytics: () => api.get('/dashboard/analytics/ranks'),
}

export const reportsAPI = {
  getFullReport: (candidateId) => api.get(`/reports/candidate/${candidateId}/full`),
  getRanking: (jobId) => api.get('/reports/ranking', { params: jobId ? { job_id: jobId } : {} }),
}

export const usersAPI = {
  list: (params) => api.get('/users/', { params }),
  get: (id) => api.get(`/users/${id}`),
  delete: (id) => api.delete(`/users/${id}`),
}
