import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/features/auth'

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
      path: '/',
      redirect: '/login',
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/patients',
      name: 'patients',
      component: () => import('@/views/PatientsPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/doctors',
      name: 'doctors',
      component: () => import('@/views/DoctorsPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/appointments',
      name: 'appointments',
      component: () => import('@/features/appointments/pages/AppointmentsPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/timeslots',
      name: 'timeslots',
      component: () => import('@/views/TimeSlotsPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/records',
      name: 'records',
      component: () => import('@/views/RecordsPage.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/profile',
      name: 'profile',
      component: () => import('@/views/ProfilePage.vue'),
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/dashboard')
  } else {
    next()
  }
})

export default router
