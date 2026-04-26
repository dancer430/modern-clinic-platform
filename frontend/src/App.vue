<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth'
import type { Role } from '@/features/auth'
import BrandLogo from '@/components/BrandLogo.vue'
import { usePlatformBrand } from '@/composables/usePlatformBrand'
import { Odometer, User, UserFilled, Calendar, Clock, Document, SwitchButton } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const { platformName, loadPlatformBrand } = usePlatformBrand()

const showShell = computed(() => authStore.isAuthenticated && route.path !== '/login')

interface NavItem {
  path: string
  label: string
  icon: unknown
  roles?: Array<Role>
}

const navItems: Array<NavItem> = [
  { path: '/dashboard', label: 'Dashboard', icon: Odometer },
  { path: '/doctors', label: 'Doctors', icon: User },
  { path: '/patients', label: 'Patients', icon: UserFilled },
  { path: '/appointments', label: 'Appointments', icon: Calendar },
  { path: '/timeslots', label: 'My Schedule', icon: Clock, roles: ['doctor', 'admin'] },
  { path: '/records', label: 'Medical Records', icon: Document, roles: ['doctor', 'admin'] },
]

const visibleNavItems = computed(() =>
  navItems.filter((item) => {
    if (!item.roles) return true
    const role = authStore.user?.user_type
    if (!role) return false
    return item.roles.includes(role)
  }),
)

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
          <router-link v-for="item in visibleNavItems" :key="item.path" :to="item.path" class="nav-link">
            <el-icon class="nav-emoji"><component :is="item.icon" /></el-icon>
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
          <el-button class="footer-logout" title="Logout" aria-label="Logout" @click.stop="handleLogout">
            <el-icon><SwitchButton /></el-icon>
          </el-button>
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
