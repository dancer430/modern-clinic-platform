import { describe, it, expect, beforeEach, vi } from 'vitest'

import {
  clearHttpAuthHandlers,
  getHttpAuthHandlers,
  registerHttpAuthHandlers,
} from '../auth-bridge'

describe('shared/http auth-bridge', () => {
  beforeEach(() => {
    clearHttpAuthHandlers()
  })

  it('returns null until handlers are registered', () => {
    expect(getHttpAuthHandlers()).toBeNull()
  })

  it('registers and clears handlers', () => {
    const handlers = {
      getAccessToken: vi.fn(() => 'tok'),
      refreshAccessToken: vi.fn(() => Promise.resolve('new-tok')),
      onAuthFailure: vi.fn(),
    }
    registerHttpAuthHandlers(handlers)
    expect(getHttpAuthHandlers()).toBe(handlers)

    clearHttpAuthHandlers()
    expect(getHttpAuthHandlers()).toBeNull()
  })

  it('overwrites a previously registered handler set on re-register', () => {
    const first = {
      getAccessToken: vi.fn(),
      refreshAccessToken: vi.fn(() => Promise.resolve('a')),
      onAuthFailure: vi.fn(),
    }
    const second = {
      getAccessToken: vi.fn(),
      refreshAccessToken: vi.fn(() => Promise.resolve('b')),
      onAuthFailure: vi.fn(),
    }
    registerHttpAuthHandlers(first)
    registerHttpAuthHandlers(second)
    expect(getHttpAuthHandlers()).toBe(second)
  })
})
