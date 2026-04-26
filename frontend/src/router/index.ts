import { ElMessage } from 'element-plus'
import {
  createRouter,
  createWebHistory,
  type NavigationGuardNext,
  type RouteLocationNormalized,
} from 'vue-router'

import { useAuthStore } from '@/features/auth'
import type { Role } from '@/features/auth'

declare module 'vue-router' {
  interface RouteMeta {
    requiresAuth?: boolean
    roles?: Array<Role>
  }
}

const ROLES_ALL: Array<Role> = ['admin', 'doctor', 'patient']
const ROLES_STAFF: Array<Role> = ['admin', 'doctor']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginPage.vue'),
      meta: { requiresAuth: false },
    },
    { path: '/', redirect: '/login' },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardPage.vue'),
      meta: { requiresAuth: true, roles: ROLES_ALL },
    },
    {
      path: '/patients',
      name: 'patients',
      component: () => import('@/views/PatientsPage.vue'),
      meta: { requiresAuth: true, roles: ROLES_ALL },
    },
    {
      path: '/doctors',
      name: 'doctors',
      component: () => import('@/views/DoctorsPage.vue'),
      meta: { requiresAuth: true, roles: ROLES_ALL },
    },
    {
      path: '/appointments',
      name: 'appointments',
      component: () => import('@/features/appointments/pages/AppointmentsPage.vue'),
      meta: { requiresAuth: true, roles: ROLES_ALL },
    },
    {
      path: '/timeslots',
      name: 'timeslots',
      component: () => import('@/views/TimeSlotsPage.vue'),
      meta: { requiresAuth: true, roles: ROLES_STAFF },
    },
    {
      path: '/records',
      name: 'records',
      component: () => import('@/views/RecordsPage.vue'),
      meta: { requiresAuth: true, roles: ROLES_STAFF },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfilePage.vue'),
      meta: { requiresAuth: true, roles: ROLES_ALL },
    },
  ],
})

export const beforeEachGuard = (
  to: RouteLocationNormalized,
  _from: RouteLocationNormalized,
  next: NavigationGuardNext,
): void => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    next('/login')
    return
  }
  if (to.path === '/login' && auth.isAuthenticated) {
    next('/dashboard')
    return
  }
  const allowed = to.meta.roles
  if (allowed && allowed.length > 0) {
    const role = auth.user?.user_type
    if (!role || !allowed.includes(role)) {
      ElMessage.warning('You do not have access to that page')
      next('/dashboard')
      return
    }
  }
  next()
}

router.beforeEach(beforeEachGuard)

export default router
