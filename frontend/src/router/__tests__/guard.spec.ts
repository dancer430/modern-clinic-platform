import { describe, it, expect, beforeEach, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'

vi.mock('element-plus', () => ({
  ElMessage: {
    warning: vi.fn(),
  },
}))

import { ElMessage } from 'element-plus'
const messageWarningMock = vi.mocked(ElMessage.warning)

import { useAuthStore } from '@/features/auth'
import { beforeEachGuard } from '../index'
import type { RouteLocationNormalized } from 'vue-router'

const buildRoute = (path: string, meta: Record<string, unknown> = {}): RouteLocationNormalized =>
  ({
    fullPath: path,
    path,
    query: {},
    hash: '',
    matched: [],
    meta,
    name: undefined,
    params: {},
    redirectedFrom: undefined,
  } as unknown as RouteLocationNormalized)

describe('beforeEachGuard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    messageWarningMock.mockClear()
  })

  it('redirects unauthenticated user to /login when route requires auth', () => {
    const next = vi.fn()
    beforeEachGuard(
      buildRoute('/timeslots', { requiresAuth: true, roles: ['doctor', 'admin'] }),
      buildRoute('/'),
      next,
    )
    expect(next).toHaveBeenCalledWith('/login')
  })

  it('bounces authenticated user away from /login', () => {
    const auth = useAuthStore()
    auth.token = 'tok'
    auth.user = { id: 1, username: 'a', email: 'a', name: 'a', user_type: 'admin', phone: '' }

    const next = vi.fn()
    beforeEachGuard(buildRoute('/login', { requiresAuth: false }), buildRoute('/'), next)
    expect(next).toHaveBeenCalledWith('/dashboard')
  })

  it('rejects role mismatch back to /dashboard with a toast', () => {
    const auth = useAuthStore()
    auth.token = 'tok'
    auth.user = { id: 2, username: 'p', email: 'p', name: 'p', user_type: 'patient', phone: '' }

    const next = vi.fn()
    beforeEachGuard(
      buildRoute('/timeslots', { requiresAuth: true, roles: ['doctor', 'admin'] }),
      buildRoute('/dashboard'),
      next,
    )
    expect(next).toHaveBeenCalledWith('/dashboard')
    expect(messageWarningMock).toHaveBeenCalledTimes(1)
  })

  it('passes role match through', () => {
    const auth = useAuthStore()
    auth.token = 'tok'
    auth.user = { id: 3, username: 'd', email: 'd', name: 'd', user_type: 'doctor', phone: '' }

    const next = vi.fn()
    beforeEachGuard(
      buildRoute('/timeslots', { requiresAuth: true, roles: ['doctor', 'admin'] }),
      buildRoute('/dashboard'),
      next,
    )
    expect(next).toHaveBeenCalledWith()
    expect(messageWarningMock).not.toHaveBeenCalled()
  })

  it('does not gate routes without `roles`', () => {
    const auth = useAuthStore()
    auth.token = 'tok'
    auth.user = { id: 4, username: 'p', email: 'p', name: 'p', user_type: 'patient', phone: '' }

    const next = vi.fn()
    beforeEachGuard(
      buildRoute('/dashboard', { requiresAuth: true }),
      buildRoute('/'),
      next,
    )
    expect(next).toHaveBeenCalledWith()
  })
})
