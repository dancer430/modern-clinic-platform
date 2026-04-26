import httpClient from '@/shared/http'

import type { AuthSession, LoginCredentials, RefreshResponse } from '../types'

export const loginRequest = async (credentials: LoginCredentials): Promise<AuthSession> => {
  const response = await httpClient.post<AuthSession>('/api/auth/login/', {
    username: credentials.account,
    password: credentials.password,
  })
  return response.data
}

export const refreshRequest = async (refreshToken: string): Promise<RefreshResponse> => {
  const response = await httpClient.post<RefreshResponse>(
    '/api/auth/refresh/',
    { refresh: refreshToken },
  )
  return response.data
}

export const logoutRequest = async (refreshToken: string | null): Promise<void> => {
  if (!refreshToken) return
  await httpClient.post('/api/auth/logout/', { refresh: refreshToken })
}
