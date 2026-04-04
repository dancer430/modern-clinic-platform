import axios from 'axios'

const runtimeOrigin = typeof window !== 'undefined' ? window.location.origin : ''
const baseURL = import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? 'http://localhost:8000' : runtimeOrigin)

// Shared pending refresh promise to prevent concurrent token refreshes
let pendingRefresh: Promise<string> | null = null

export async function refreshAccessToken(): Promise<string> {
  if (pendingRefresh) {
    return pendingRefresh
  }

  const refreshToken = localStorage.getItem('refreshToken')
  if (!refreshToken) {
    return Promise.reject(new Error('No refresh token'))
  }

  pendingRefresh = axios
    .post(baseURL + '/api/auth/refresh/', { refresh: refreshToken })
    .then((response) => {
      const newAccessToken: string = response.data.access
      localStorage.setItem('accessToken', newAccessToken)
      if (response.data.refresh) {
        localStorage.setItem('refreshToken', response.data.refresh)
      }
      return newAccessToken
    })
    .finally(() => {
      pendingRefresh = null
    })

  return pendingRefresh
}

export function clearTokens() {
  localStorage.removeItem('accessToken')
  localStorage.removeItem('refreshToken')
  window.location.href = '/login'
}
