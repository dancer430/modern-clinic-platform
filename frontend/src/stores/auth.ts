import { defineStore } from 'pinia'
import apiClient from '@/utils/axios'

export interface User {
  id: number
  username: string
  email: string
  name: string
  user_type: 'admin' | 'doctor' | 'patient'
  db_vendor?: 'sqlite' | 'postgresql' | string
  phone: string
  avatar_data?: string
  avatar_type?: string
  avatar_size?: number | null
}

export interface AuthState {
  user: User | null
  token: string | null
  refreshToken: string | null
  tokenExpireTime: number | null // token 过期时间戳（毫秒）
}

// 用于存储 token 刷新定时器
let tokenRefreshTimer: number | null = null

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    token: null,
    refreshToken: null,
    tokenExpireTime: null,
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.token,
    userType: (state): string | null => state.user?.user_type || null,
    isAdmin: (state): boolean => state.user?.user_type === 'admin',
    isDoctor: (state): boolean => state.user?.user_type === 'doctor',
    isPatient: (state): boolean => state.user?.user_type === 'patient',
  },

  actions: {
    setUser(user: User | null) {
      this.user = user
      if (user) {
        localStorage.setItem('user', JSON.stringify(user))
      } else {
        localStorage.removeItem('user')
      }
    },

    async login(credentials: { account: string; password: string }) {
      console.log('[Auth Store Login]', credentials.account)
      try {
        const response = await apiClient.post('/login/', {
          username: credentials.account,
          password: credentials.password,
        })
        console.log('[Auth Store Login Success]', response.data)
        const { access, refresh, user } = response.data

        this.token = access
        this.refreshToken = refresh
        this.setUser(user)

        // 计算 token 过期时间（access token 有效期为 60 分钟）
        const expireTime = Date.now() + 60 * 60 * 1000
        this.tokenExpireTime = expireTime

        localStorage.setItem('accessToken', access)
        localStorage.setItem('refreshToken', refresh)
        localStorage.setItem('tokenExpireTime', expireTime.toString())

        // 设置定时刷新 token（在过期前 5 分钟刷新）
        scheduleTokenRefresh()

        return { success: true }
      } catch (error: any) {
        console.error('[Auth Store Login Failed]', error)
        return {
          success: false,
          error: error.response?.data?.detail || '登录失败',
        }
      }
    },

    async logout() {
      try {
        const refreshToken = localStorage.getItem('refreshToken')
        if (refreshToken) {
          await apiClient.post('/logout/', { refresh: refreshToken })
        }
      } catch (error: any) {
        console.error('Logout failed:', error)
      } finally {
        this.setUser(null)
        this.token = null
        this.refreshToken = null
        this.tokenExpireTime = null

        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')
        localStorage.removeItem('tokenExpireTime')

        // 清除 token 刷新定时器
        clearTokenRefresh()
      }
    },

    loadFromStorage() {
      const token = localStorage.getItem('accessToken')
      const refreshToken = localStorage.getItem('refreshToken')
      const userStr = localStorage.getItem('user')
      const expireTimeStr = localStorage.getItem('tokenExpireTime')

      if (token) this.token = token
      if (refreshToken) this.refreshToken = refreshToken
      if (expireTimeStr) {
        const expireTime = parseInt(expireTimeStr, 10)
        if (!isNaN(expireTime)) {
          this.tokenExpireTime = expireTime
          // 如果 token 快要过期了，设置刷新定时器
          if (expireTime > Date.now()) {
            scheduleTokenRefresh()
          }
        }
      }
      if (userStr) {
        try {
          this.user = JSON.parse(userStr)
        } catch (e) {
          console.error('Failed to parse user from storage:', e)
        }
      }
    },
  },
})

// Token 刷新函数（在 store 外部，因为需要访问外部变量）
function scheduleTokenRefresh() {
  // 清除已有的定时器
  clearTokenRefresh()

  const authStore = useAuthStore()
  if (!authStore.tokenExpireTime || !authStore.refreshToken) {
    return
  }

  const now = Date.now()
  const timeUntilExpiry = authStore.tokenExpireTime - now

  // 在过期前 5 分钟刷新
  const refreshTime = Math.max(0, timeUntilExpiry - 5 * 60 * 1000)

  console.log(`[Auth Store] Token will refresh in ${Math.round(refreshTime / 1000)}s`)

  tokenRefreshTimer = window.setTimeout(async () => {
    try {
      console.log('[Auth Store] Auto-refreshing token...')
      await refreshAccessToken()
    } catch (error) {
      console.error('[Auth Store] Auto-refresh failed:', error)
      // 如果刷新失败，登出用户
      await authStore.logout()
    }
  }, refreshTime)
}

function clearTokenRefresh() {
  if (tokenRefreshTimer !== null) {
    clearTimeout(tokenRefreshTimer)
    tokenRefreshTimer = null
  }
}

async function refreshAccessToken() {
  const authStore = useAuthStore()
  try {
    const response = await apiClient.post('/refresh/', {
      refresh: authStore.refreshToken,
    })
    
    const newAccessToken = response.data.access
    const newRefreshToken = response.data.refresh || authStore.refreshToken

    authStore.token = newAccessToken
    authStore.refreshToken = newRefreshToken

    // 更新过期时间
    const expireTime = Date.now() + 60 * 60 * 1000
    authStore.tokenExpireTime = expireTime

    // 保存到 localStorage
    localStorage.setItem('accessToken', newAccessToken)
    if (response.data.refresh) {
      localStorage.setItem('refreshToken', newRefreshToken)
    }
    localStorage.setItem('tokenExpireTime', expireTime.toString())

    console.log('[Auth Store] Token refreshed successfully')

    // 设置下一次刷新
    scheduleTokenRefresh()

    return { success: true }
  } catch (error: any) {
    console.error('[Auth Store] Token refresh failed:', error)
    return {
      success: false,
      error: error.response?.data?.detail || 'Token refresh failed',
    }
  }
}
