import { defineStore } from 'pinia'

import { loginRequest, logoutRequest } from '../api'
import { refreshAccessToken } from '../services/refresh'
import {
  REFRESH_LEAD_TIME_MS,
  clearPersistedSession,
  persistSession,
  readAccessToken,
  readPersistedSession,
} from '../services/session'
import type { LoginCredentials, User } from '../types'

interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  tokenExpireTime: number | null
}

let scheduledRefresh: ReturnType<typeof setTimeout> | null = null

const cancelScheduledRefresh = () => {
  if (scheduledRefresh !== null) {
    clearTimeout(scheduledRefresh)
    scheduledRefresh = null
  }
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: null,
    refreshToken: null,
    tokenExpireTime: null,
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.token,
    userType: (state): User['user_type'] | null => state.user?.user_type ?? null,
    isAdmin: (state): boolean => state.user?.user_type === 'admin',
    isDoctor: (state): boolean => state.user?.user_type === 'doctor',
    isPatient: (state): boolean => state.user?.user_type === 'patient',
  },

  actions: {
    setUser(user: User | null) {
      this.user = user
    },

    async login(credentials: LoginCredentials) {
      try {
        const session = await loginRequest(credentials)
        const expireTime = persistSession(session)

        this.token = session.access
        this.refreshToken = session.refresh
        this.user = session.user
        this.tokenExpireTime = expireTime

        this.scheduleRefresh()
        return { success: true as const }
      } catch (error) {
        const detail = (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
        return { success: false as const, error: detail || '登录失败' }
      }
    },

    async logout() {
      try {
        await logoutRequest(this.refreshToken)
      } catch {
        // best-effort: backend blacklists when possible; local cleanup must run
      } finally {
        this.token = null
        this.refreshToken = null
        this.user = null
        this.tokenExpireTime = null
        clearPersistedSession()
        cancelScheduledRefresh()
      }
    },

    loadFromStorage() {
      const persisted = readPersistedSession()
      this.token = persisted.accessToken
      this.refreshToken = persisted.refreshToken
      this.tokenExpireTime = persisted.tokenExpireTime
      this.user = persisted.user
      if (this.tokenExpireTime && this.tokenExpireTime > Date.now()) {
        this.scheduleRefresh()
      }
    },

    scheduleRefresh() {
      cancelScheduledRefresh()
      if (!this.tokenExpireTime || !this.refreshToken) return
      const delay = Math.max(0, this.tokenExpireTime - Date.now() - REFRESH_LEAD_TIME_MS)
      scheduledRefresh = setTimeout(async () => {
        try {
          const access = await refreshAccessToken()
          this.token = access
          // refresh.ts already persisted the new tokens and the new expire
          // time; mirror them into the store so derived getters stay correct.
          const persisted = readPersistedSession()
          this.tokenExpireTime = persisted.tokenExpireTime
          if (persisted.refreshToken) this.refreshToken = persisted.refreshToken
          this.scheduleRefresh()
        } catch {
          await this.logout()
        }
      }, delay)
    },

    syncTokenFromStorage() {
      this.token = readAccessToken()
    },
  },
})
