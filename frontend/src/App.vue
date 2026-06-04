<script setup lang="ts">
import { computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/features/auth'
import type { Role } from '@/features/auth'
import BrandLogo from '@/components/BrandLogo.vue'
import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import { elementLocale } from '@/i18n'
import { usePlatformBrand } from '@/composables/usePlatformBrand'
import { DataLine, FirstAidKit, User, Calendar, Timer, Notebook, SwitchButton, OfficeBuilding, Memo, Edit } from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const { platformName, loadPlatformBrand } = usePlatformBrand()

const showShell = computed(() => authStore.isAuthenticated && route.path !== '/login')

interface NavItem {
  path: string
  labelKey: string
  icon: unknown
  roles?: Array<Role>
}

const navItems: Array<NavItem> = [
  { path: '/dashboard', labelKey: 'nav.dashboard', icon: DataLine },
  { path: '/doctors', labelKey: 'nav.doctors', icon: FirstAidKit },
  { path: '/patients', labelKey: 'nav.patients', icon: User },
  { path: '/appointments', labelKey: 'nav.appointments', icon: Calendar },
  { path: '/timeslots', labelKey: 'nav.schedule', icon: Timer, roles: ['doctor', 'admin'] },
  { path: '/records', labelKey: 'nav.records', icon: Notebook, roles: ['doctor', 'admin'] },
  { path: '/admin/departments', labelKey: 'nav.departments', icon: OfficeBuilding, roles: ['admin'] },
  { path: '/admin/doctor-profiles', labelKey: 'nav.doctorProfiles', icon: FirstAidKit, roles: ['admin'] },
  { path: '/admin/reviews', labelKey: 'nav.pendingReviews', icon: Memo, roles: ['admin'] },
  { path: '/doctor/profile', labelKey: 'nav.myPublicProfile', icon: Edit, roles: ['doctor'] },
]

const visibleNavItems = computed(() =>
  navItems.filter((item) => {
    if (!item.roles) return true
    const role = authStore.user?.user_type
    if (!role) return false
    return item.roles.includes(role)
  }),
)

const currentPageTitle = computed(() => {
  const routeName = String(route.name || '')
  if (!routeName) return t('nav.workspace')
  const key = `pageTitle.${routeName}`
  const translated = t(key)
  return translated === key ? t('nav.workspace') : translated
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
  <el-config-provider :locale="elementLocale">
  <div class="app-shell">
    <template v-if="showShell">
      <aside class="shell-sidebar">
        <router-link to="/dashboard" class="sidebar-brand">
          <BrandLogo size="sm" monochrome />
        </router-link>

        <nav class="sidebar-nav">
          <router-link v-for="item in visibleNavItems" :key="item.path" :to="item.path" class="nav-link">
            <el-icon class="nav-emoji"><component :is="item.icon" /></el-icon>
            <span class="nav-text">{{ t(item.labelKey) }}</span>
          </router-link>
        </nav>

        <div class="sidebar-lang">
          <LanguageSwitcher />
        </div>

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
            <strong>{{ authStore.user?.username || t('nav.demoUser') }}</strong>
            <span>{{ authStore.user?.user_type || 'admin' }}</span>
          </div>
          <el-button class="footer-logout" :title="t('nav.logout')" :aria-label="t('nav.logout')" @click.stop="handleLogout">
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

    <template v-else>
      <div class="lang-floating">
        <LanguageSwitcher />
      </div>
      <main class="login-host">
        <router-view />
      </main>
    </template>
  </div>
  </el-config-provider>
</template>

<style scoped>
.sidebar-lang {
  padding: 12px 16px 4px;
  margin-top: auto;
}
.sidebar-lang + .sidebar-footer {
  margin-top: 0;
}
.lang-floating {
  position: fixed;
  top: 18px;
  right: 22px;
  z-index: 50;
}
</style>
