import axios, { type AxiosInstance, type InternalAxiosRequestConfig } from 'axios'

import { getHttpAuthHandlers } from './auth-bridge'

const runtimeOrigin = typeof window !== 'undefined' ? window.location.origin : ''

export const resolveApiBaseUrl = (): string =>
  import.meta.env.VITE_API_BASE_URL ||
  (import.meta.env.DEV ? 'http://localhost:8000' : runtimeOrigin)

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean
  _skipAuth?: boolean
}

export const httpClient: AxiosInstance = axios.create({
  baseURL: resolveApiBaseUrl(),
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

const isAuthEndpoint = (url: string | undefined, suffix: string): boolean =>
  !!url && (url === suffix || url.endsWith(suffix))

httpClient.interceptors.request.use((config) => {
  const retriable = config as RetriableConfig
  if (retriable._skipAuth) {
    return config
  }
  // Login and refresh must never carry a stale token: the backend would
  // otherwise reject the (still-valid) refresh request with the access-token
  // 401 before SimpleJWT even looks at the refresh body.
  if (isAuthEndpoint(config.url, '/api/auth/login/') || isAuthEndpoint(config.url, '/api/auth/refresh/')) {
    return config
  }
  const handlers = getHttpAuthHandlers()
  const token = handlers?.getAccessToken() ?? null
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

httpClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as RetriableConfig | undefined
    if (!originalRequest || originalRequest._skipAuth) {
      return Promise.reject(error)
    }
    if (isAuthEndpoint(originalRequest.url, '/api/auth/login/')) {
      return Promise.reject(error)
    }
    const handlers = getHttpAuthHandlers()
    if (!handlers || error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error)
    }

    originalRequest._retry = true
    try {
      const newAccessToken = await handlers.refreshAccessToken()
      originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
      return httpClient(originalRequest)
    } catch (refreshError) {
      handlers.onAuthFailure()
      return Promise.reject(refreshError)
    }
  },
)

export default httpClient
