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
  create: (data) => api.post('/candidates/', data),
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
    timeout: 150000,
  }),
}

export const pipelineAPI = {
  list: (params) => api.get('/pipeline/', { params }),
  updateStage: (candidateId, stage) => api.patch(`/pipeline/candidates/${candidateId}/stage`, { stage }),
  history: (candidateId) => api.get(`/pipeline/candidates/${candidateId}/history`),
}

export const interviewsAPI = {
  list: (params) => api.get('/interviews/', { params }),
  get: (id) => api.get(`/interviews/${id}`),
  create: (data) => api.post('/interviews/', data),
  update: (id, data) => api.patch(`/interviews/${id}`, data),
  cancel: (id) => api.post(`/interviews/${id}/cancel`),
  complete: (id) => api.post(`/interviews/${id}/complete`),
  saveFeedback: (id, data) => api.put(`/interviews/${id}/feedback`, data),
  getFeedback: (id) => api.get(`/interviews/${id}/feedback`),
}

export const aiInterviewsAPI = {
  candidates: (params) => api.get('/ai-interviews/candidates', { params }),
  jobs: (params) => api.get('/ai-interviews/jobs', { params }),
  list: (params) => api.get('/ai-interviews/sessions', { params }),
  get: (id) => api.get(`/ai-interviews/sessions/${id}`),
  create: (data) => api.post('/ai-interviews/sessions', data),
  generate: (id) => api.post(`/ai-interviews/sessions/${id}/generate`),
  start: (id) => api.post(`/ai-interviews/sessions/${id}/start`),
  pause: (id) => api.post(`/ai-interviews/sessions/${id}/pause`),
  saveAnswer: (id, questionId, data) => api.put(`/ai-interviews/sessions/${id}/questions/${questionId}/answer`, data),
  transcribeAnswer: (id, questionId, blob, durationSeconds) => {
    const formData = new FormData()
    formData.append('audio', blob, `interview-answer.${blob.type.includes('ogg') ? 'ogg' : blob.type.includes('mp4') ? 'mp4' : 'webm'}`)
    formData.append('duration_seconds', String(durationSeconds))
    return api.post(`/ai-interviews/sessions/${id}/questions/${questionId}/transcribe`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 90000,
    })
  },
  evaluateAnswer: (id, questionId) => api.post(`/ai-interviews/sessions/${id}/questions/${questionId}/evaluate`),
  followUp: (id, questionId) => api.post(`/ai-interviews/sessions/${id}/questions/${questionId}/follow-up`),
  appendLiveFollowUp: (id, questionId) => api.post(`/ai-interviews/sessions/${id}/questions/${questionId}/live-follow-up`),
  complete: (id) => api.post(`/ai-interviews/sessions/${id}/complete`),
  report: (id) => api.get(`/ai-interviews/sessions/${id}/report`),
  review: (id, data) => api.patch(`/ai-interviews/sessions/${id}/review`, data),
}

export const dashboardAPI = {
  getStats: () => api.get('/dashboard/stats'),
  getSkillAnalytics: () => api.get('/dashboard/analytics/skills'),
  getRankAnalytics: () => api.get('/dashboard/analytics/ranks'),
}

export const reportsAPI = {
  getFullReport: (candidateId) => api.get(`/reports/candidate/${candidateId}/full`),
  getRanking: (jobId) => api.get('/reports/ranking', { params: jobId ? { job_id: jobId } : {} }),
  compareCandidates: (candidateIds) => {
    const params = new URLSearchParams()
    candidateIds.forEach((id) => params.append('candidate_ids', id))
    return api.get(`/reports/compare?${params.toString()}`)
  },
}

export const usersAPI = {
  list: (params) => api.get('/users/', { params }),
  get: (id) => api.get(`/users/${id}`),
  delete: (id) => api.delete(`/users/${id}`),
}
