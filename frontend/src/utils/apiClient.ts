import axios from 'axios'

const runtimeOrigin = typeof window !== 'undefined' ? window.location.origin : ''
const baseURL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : runtimeOrigin)

export const apiClient = axios.create({
  baseURL: baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    if (error.response?.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        originalRequest._retry = true
        try {
          const response = await axios.post(baseURL + '/api/auth/refresh/', {
            refresh: refreshToken,
          })
          const newAccessToken = response.data.access
          localStorage.setItem('accessToken', newAccessToken)
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          return apiClient(originalRequest)
        } catch (refreshError) {
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
          window.location.href = '/login'
          return Promise.reject(refreshError)
        }
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
