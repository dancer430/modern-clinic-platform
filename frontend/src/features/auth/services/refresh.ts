import { refreshRequest } from '../api'

import {
  persistRefreshedTokens,
  readRefreshToken,
} from './session'

let pending: Promise<string> | null = null

// One pending refresh promise across the whole app. Concurrent 401s — from
// any number of simultaneous requests — wait on the same promise instead of
// triggering parallel refresh calls (which would race the backend's
// rotate-and-blacklist policy and log everyone out).
export const refreshAccessToken = async (): Promise<string> => {
  if (pending) {
    return pending
  }
  const refreshToken = readRefreshToken()
  if (!refreshToken) {
    return Promise.reject(new Error('No refresh token'))
  }

  pending = refreshRequest(refreshToken)
    .then((response) => {
      persistRefreshedTokens(response)
      return response.access
    })
    .finally(() => {
      pending = null
    })

  return pending
}

export const __resetPendingForTests = (): void => {
  pending = null
}
