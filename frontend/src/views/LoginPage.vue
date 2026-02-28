<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import BrandLogo from '@/components/BrandLogo.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)

const form = reactive({
  account: 'admin',
  password: 'admin123456',
})

const login = async () => {
  loading.value = true
  const result = await authStore.login({
    account: form.account,
    password: form.password,
  })
  loading.value = false

  if (result.success) {
    router.push('/dashboard')
    return
  }

  window.alert(result.error || 'Login failed')
}
</script>

<template>
  <div class="login-page">
    <section class="login-brand">
      <div class="login-logo-wrap">
        <BrandLogo size="lg" />
      </div>
      <div class="login-hero">
        <h1>Streamline Your Medical Practice</h1>
        <p>Manage doctors, patients, and appointments all in one place.</p>
      </div>
    </section>

    <section class="login-form-area">
      <div class="login-card">
        <h2>Welcome back</h2>
        <p>Sign in to your account to continue</p>

        <form @submit.prevent="login" class="login-form">
          <label>Username or Email</label>
          <input v-model="form.account" type="text" autocomplete="username" placeholder="Enter username or email" />

          <label>Password</label>
          <input v-model="form.password" type="password" autocomplete="current-password" placeholder="Enter password" />

          <button type="submit" class="btn-primary" :disabled="loading">{{ loading ? 'Signing In...' : 'Sign In' }}</button>
        </form>
      </div>
    </section>
  </div>
</template>
