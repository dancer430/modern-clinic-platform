import axios from 'axios'

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
  (response) => {
    console.log('[Axios Response Success]', response.config.url, response.status)
    return response
  },
  async (error) => {
    const originalRequest = error.config
    console.log('[Axios Response Error]', originalRequest.url, error.response?.status)
    // 排除登录接口 - 登录失败不应触发 token 刷新
    if (originalRequest.url === '/login/' || originalRequest.url?.endsWith('/login/') || originalRequest.url?.includes('/login/')) {
      console.log('[Skipping token refresh for login endpoint]')
      return Promise.reject(error)
    }
    if (error.response?.status === 401 && !originalRequest._retry) {
      console.log('[Attempting token refresh]', originalRequest._retry)
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
          console.log('[Token refreshed, retrying request]')
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
