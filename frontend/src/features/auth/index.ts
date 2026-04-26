// Public surface of the auth feature. Other features and the app shell
// MUST import from here, not from auth's internal subpaths.

import { registerHttpAuthHandlers } from '@/shared/http'

import { refreshAccessToken } from './services/refresh'
import { readAccessToken } from './services/session'
import { useAuthStore } from './store'

export { useAuthStore } from './store'
export type { LoginCredentials, Role, User } from './types'

let installed = false

// Register the HTTP↔auth bridge once per app lifetime, restore persisted
// session into the pinia store, and arm the refresh scheduler. Call once
// from app/main during bootstrap.
export const setupAuth = (): void => {
  if (installed) return
  installed = true

  registerHttpAuthHandlers({
    getAccessToken: () => readAccessToken(),
    refreshAccessToken: () => refreshAccessToken(),
    onAuthFailure: () => {
      const store = useAuthStore()
      void store.logout().finally(() => {
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          window.location.href = '/login'
        }
      })
    },
  })

  const store = useAuthStore()
  store.loadFromStorage()
  if (store.tokenExpireTime && store.tokenExpireTime > Date.now()) {
    store.scheduleRefresh()
  }
}
