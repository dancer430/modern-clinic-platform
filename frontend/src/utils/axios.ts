import axios from 'axios'
import { refreshAccessToken, clearTokens } from './tokenRefresh'

const runtimeOrigin = typeof window !== 'undefined' ? window.location.origin : ''
const baseURL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : runtimeOrigin)

const apiClient = axios.create({
  baseURL: baseURL + '/api/auth/',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

apiClient.interceptors.request.use(
  (config) => {
    // 登录、刷新 token 时不要带旧 token，否则后端会先校验旧 token 返回 401
    const isLogin = config.url === '/login/' || (config.url && config.url.endsWith('/login/'))
    const isRefresh = config.url === '/refresh/' || (config.url && config.url.endsWith('/refresh/'))
    if (isLogin || isRefresh) {
      return config
    }
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
    // 排除登录接口 - 登录失败不应触发 token 刷新
    if (originalRequest.url === '/login/' || originalRequest.url?.endsWith('/login/') || originalRequest.url?.includes('/login/')) {
      return Promise.reject(error)
    }
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      try {
        const newAccessToken = await refreshAccessToken()
        originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
        return apiClient(originalRequest)
      } catch {
        clearTokens()
        return Promise.reject(error)
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient
