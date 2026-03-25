<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BrandLogo from '@/components/BrandLogo.vue'
import { usePlatformBrand } from '@/composables/usePlatformBrand'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { platformName, loadPlatformBrand } = usePlatformBrand()

const showShell = computed(() => authStore.isAuthenticated && route.path !== '/login')

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/doctors', label: 'Doctors', icon: '👨‍⚕️' },
  { path: '/patients', label: 'Patients', icon: '🧑‍🤝‍🧑' },
  { path: '/appointments', label: 'Appointments', icon: '📅' },
  { path: '/timeslots', label: 'My Schedule', icon: '🕒' },
  { path: '/records', label: 'Medical Records', icon: '📋' },
]

const pageTitleMap: Record<string, string> = {
  login: 'Sign In',
  dashboard: 'Dashboard',
  doctors: 'Doctors',
  patients: 'Patients',
  appointments: 'Appointments',
  timeslots: 'Schedule',
  records: 'Medical Records',
  profile: 'Personal Center',
}

const currentPageTitle = computed(() => {
  const routeName = String(route.name || '')
  return pageTitleMap[routeName] || 'Workspace'
})

const handleLogout = async () => {
  await authStore.logout()
  router.push('/login')
}

const openProfile = () => {
  router.push('/profile')
}

onMounted(async () => {
  await loadPlatformBrand()
})

watch(
  [platformName, currentPageTitle],
  () => {
    document.title = `${platformName.value} - ${currentPageTitle.value}`
  },
  { immediate: true }
)
</script>

<template>
  <div class="app-shell">
    <template v-if="showShell">
      <aside class="shell-sidebar">
        <router-link to="/dashboard" class="sidebar-brand">
          <BrandLogo size="sm" monochrome />
        </router-link>

        <nav class="sidebar-nav">
          <router-link v-for="item in navItems" :key="item.path" :to="item.path" class="nav-link">
            <span class="nav-emoji">{{ item.icon }}</span>
            <span class="nav-text">{{ item.label }}</span>
          </router-link>
        </nav>

        <div class="sidebar-footer" @click="openProfile">
          <span class="avatar-chip">
            <img
              v-if="authStore.user?.avatar_data"
              :src="authStore.user.avatar_data"
              alt="avatar"
              class="avatar-image"
            />
            <template v-else>{{ authStore.user?.name?.[0] || authStore.user?.username?.[0] || 'U' }}</template>
          </span>
          <div class="user-meta">
            <strong>{{ authStore.user?.username || 'demo_user' }}</strong>
            <span>{{ authStore.user?.user_type || 'admin' }}</span>
          </div>
          <button class="btn-secondary footer-logout" title="Logout" aria-label="Logout" @click.stop="handleLogout">
            <svg class="logout-icon" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M10 17l1.4-1.4-2.6-2.6H20v-2H8.8l2.6-2.6L10 7l-5 5 5 5z" />
              <path d="M18 19h-6v2h6c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2h-6v2h6v14z" />
            </svg>
          </button>
        </div>
      </aside>

      <section class="shell-main">
        <main class="shell-content">
          <router-view />
        </main>
      </section>
    </template>

    <main v-else class="login-host">
      <router-view />
    </main>
  </div>
</template>
