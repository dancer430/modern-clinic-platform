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
import router from '@/router'
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

  it('rejects role mismatch: patient hitting staff route is redirected to /home with a toast', () => {
    const auth = useAuthStore()
    auth.token = 'tok'
    auth.user = { id: 2, username: 'p', email: 'p', name: 'p', user_type: 'patient', phone: '' }

    const next = vi.fn()
    beforeEachGuard(
      buildRoute('/timeslots', { requiresAuth: true, roles: ['doctor', 'admin'] }),
      buildRoute('/dashboard'),
      next,
    )
    expect(next).toHaveBeenCalledWith('/home')
    expect(messageWarningMock).toHaveBeenCalledTimes(1)
  })

  it('patient hitting /dashboard is redirected to /home', () => {
    const auth = useAuthStore()
    auth.token = 'tok'
    auth.user = { id: 5, username: 'pat', email: 'pat', name: 'pat', user_type: 'patient', phone: '' }

    const next = vi.fn()
    beforeEachGuard(
      buildRoute('/dashboard', { requiresAuth: true, roles: ['admin', 'doctor'] }),
      buildRoute('/home'),
      next,
    )
    expect(next).toHaveBeenCalledWith('/home')
    expect(messageWarningMock).toHaveBeenCalledTimes(1)
  })

  it('authenticated patient on /login is redirected to /home', () => {
    const auth = useAuthStore()
    auth.token = 'tok'
    auth.user = { id: 6, username: 'pat2', email: 'pat2', name: 'pat2', user_type: 'patient', phone: '' }

    const next = vi.fn()
    beforeEachGuard(buildRoute('/login', { requiresAuth: false }), buildRoute('/'), next)
    expect(next).toHaveBeenCalledWith('/home')
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

  it('gates /doctors and /patients to admin only', () => {
    const routes = router.getRoutes()
    const doctors = routes.find((r) => r.name === 'doctors')
    const patients = routes.find((r) => r.name === 'patients')
    expect(doctors?.meta.roles).toEqual(['admin'])
    expect(patients?.meta.roles).toEqual(['admin'])
  })
})
