// Shared HTTP transport must be able to attach an access token to outgoing
// requests and to coordinate a refresh on 401 — but the *source of truth*
// for tokens and the refresh endpoint live in features/auth. To keep the
// dependency direction one-way (features depend on shared, not the other
// way), the auth feature registers callbacks here at app startup.

export interface HttpAuthHandlers {
  getAccessToken: () => string | null
  refreshAccessToken: () => Promise<string>
  onAuthFailure: () => void
}

let registered: HttpAuthHandlers | null = null

export const registerHttpAuthHandlers = (handlers: HttpAuthHandlers): void => {
  registered = handlers
}

export const clearHttpAuthHandlers = (): void => {
  registered = null
}

export const getHttpAuthHandlers = (): HttpAuthHandlers | null => registered
