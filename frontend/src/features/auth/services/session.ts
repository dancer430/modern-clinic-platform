import type { AuthSession, RefreshResponse, User } from '../types'

const ACCESS_TOKEN_KEY = 'accessToken'
const REFRESH_TOKEN_KEY = 'refreshToken'
const TOKEN_EXPIRE_KEY = 'tokenExpireTime'
const USER_KEY = 'user'

// Access tokens issued by the backend live for 60 minutes (config/settings.py
// SIMPLE_JWT.ACCESS_TOKEN_LIFETIME). The session service persists this
// constant so refresh scheduling stays decoupled from the JWT body parsing.
export const ACCESS_TOKEN_LIFETIME_MS = 60 * 60 * 1000
export const REFRESH_LEAD_TIME_MS = 5 * 60 * 1000

export interface PersistedSession {
  accessToken: string | null
  refreshToken: string | null
  tokenExpireTime: number | null
  user: User | null
}

const safeJsonParse = <T>(raw: string | null): T | null => {
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

export const readPersistedSession = (): PersistedSession => {
  const expireRaw = localStorage.getItem(TOKEN_EXPIRE_KEY)
  const expire = expireRaw ? Number.parseInt(expireRaw, 10) : Number.NaN
  return {
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
    tokenExpireTime: Number.isFinite(expire) ? expire : null,
    user: safeJsonParse<User>(localStorage.getItem(USER_KEY)),
  }
}

export const persistSession = (session: AuthSession): number => {
  const expireTime = Date.now() + ACCESS_TOKEN_LIFETIME_MS
  localStorage.setItem(ACCESS_TOKEN_KEY, session.access)
  localStorage.setItem(REFRESH_TOKEN_KEY, session.refresh)
  localStorage.setItem(TOKEN_EXPIRE_KEY, expireTime.toString())
  localStorage.setItem(USER_KEY, JSON.stringify(session.user))
  return expireTime
}

export const persistRefreshedTokens = (response: RefreshResponse): number => {
  const expireTime = Date.now() + ACCESS_TOKEN_LIFETIME_MS
  localStorage.setItem(ACCESS_TOKEN_KEY, response.access)
  if (response.refresh) {
    localStorage.setItem(REFRESH_TOKEN_KEY, response.refresh)
  }
  localStorage.setItem(TOKEN_EXPIRE_KEY, expireTime.toString())
  return expireTime
}

export const clearPersistedSession = (): void => {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(TOKEN_EXPIRE_KEY)
  localStorage.removeItem(USER_KEY)
}

export const readAccessToken = (): string | null => localStorage.getItem(ACCESS_TOKEN_KEY)
export const readRefreshToken = (): string | null => localStorage.getItem(REFRESH_TOKEN_KEY)
