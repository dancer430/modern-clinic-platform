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
const ROLES_ADMIN: Array<Role> = ['admin']
const ROLES_DOCTOR: Array<Role> = ['doctor']
const ROLES_PATIENT: Array<Role> = ['patient']

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginPage.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/portal/departments',
      name: 'portal-department-list',
      component: () => import('@/features/content/pages/portal/PortalDepartmentList.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/portal/departments/:slug',
      name: 'portal-department-detail',
      component: () => import('@/features/content/pages/portal/PortalDepartmentDetail.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/portal/doctors',
      name: 'portal-doctor-list',
      component: () => import('@/features/content/pages/portal/PortalDoctorList.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/portal/doctors/:userId',
      name: 'portal-doctor-detail',
      component: () => import('@/features/content/pages/portal/PortalDoctorDetail.vue'),
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
      meta: { requiresAuth: true, roles: ROLES_ADMIN },
    },
    {
      path: '/doctors',
      name: 'doctors',
      component: () => import('@/views/DoctorsPage.vue'),
      meta: { requiresAuth: true, roles: ROLES_ADMIN },
    },
    {
      path: '/home',
      name: 'patient-home',
      component: () => import('@/views/PatientHomePage.vue'),
      meta: { requiresAuth: true, roles: ROLES_PATIENT },
    },
    {
      path: '/doctors/:id',
      name: 'doctor-detail',
      component: () => import('@/features/content/pages/admin/DoctorDetailPage.vue'),
      meta: { requiresAuth: true, roles: ROLES_ADMIN },
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
    {
      path: '/admin/departments',
      name: 'admin-department-list',
      component: () => import('@/features/content/pages/admin/AdminDepartmentList.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    {
      path: '/admin/departments/:id',
      name: 'admin-department-edit',
      component: () => import('@/features/content/pages/admin/AdminDepartmentEdit.vue'),
      meta: { requiresAuth: true, roles: ['admin'] },
    },
    { path: '/admin/doctor-profiles', redirect: '/doctors' },
    { path: '/admin/doctor-profiles/:userId', redirect: (to) => `/doctors/${to.params.userId}` },
    { path: '/admin/reviews', redirect: '/doctors' },
    {
      path: '/doctor/profile',
      name: 'doctor-my-profile',
      component: () => import('@/features/content/pages/doctor/DoctorMyProfile.vue'),
      meta: { requiresAuth: true, roles: ['doctor'] },
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
