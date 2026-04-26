<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import BrandLogo from '@/components/BrandLogo.vue'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  account: 'admin',
  password: 'admin123456',
})

const rules = reactive<FormRules>({
  account: [{ required: true, message: 'Please enter username or email', trigger: 'blur' }],
  password: [{ required: true, message: 'Please enter password', trigger: 'blur' }],
})

const login = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

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

  ElMessage.error(result.error || 'Login failed')
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

        <ElForm
          ref="formRef"
          :model="form"
          :rules="rules"
          class="login-form"
          @submit.prevent="login"
        >
          <ElFormItem label="Username or Email" prop="account">
            <ElInput
              v-model="form.account"
              autocomplete="username"
              placeholder="Enter username or email"
            />
          </ElFormItem>

          <ElFormItem label="Password" prop="password">
            <ElInput
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              placeholder="Enter password"
              show-password
            />
          </ElFormItem>

          <ElFormItem>
            <ElButton
              type="primary"
              :loading="loading"
              native-type="submit"
              class="btn-primary"
            >
              Sign In
            </ElButton>
          </ElFormItem>
        </ElForm>
      </div>
    </section>
  </div>
</template>
