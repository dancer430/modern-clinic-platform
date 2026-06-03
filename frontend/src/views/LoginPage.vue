<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/features/auth'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import BrandLogo from '@/components/BrandLogo.vue'
import DepartmentCarousel from '@/features/content/components/DepartmentCarousel.vue'

const router = useRouter()
const { t } = useI18n()
const authStore = useAuthStore()
const loading = ref(false)
const formRef = ref<FormInstance>()

const form = reactive({
  account: 'admin',
  password: 'admin123456',
})

const rules = reactive<FormRules>({
  account: [{ required: true, message: () => t('auth.pleaseEnterUsername'), trigger: 'blur' }],
  password: [{ required: true, message: () => t('auth.pleaseEnterPassword'), trigger: 'blur' }],
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

  ElMessage.error(result.error || t('auth.loginFailed'))
}
</script>

<template>
  <div class="login-page">
    <section class="login-brand">
      <div class="login-logo-wrap">
        <BrandLogo size="lg" />
      </div>
      <div class="login-hero">
        <h1>{{ t('auth.streamlineTitle') }}</h1>
        <p>{{ t('auth.streamlineSubtitle') }}</p>
      </div>

      <div class="login-portal-preview">
        <DepartmentCarousel />
        <div class="login-portal-cta">
          <ElButton class="cta-btn" @click="router.push('/portal/departments')">{{ t('auth.browseDepartments') }}</ElButton>
          <ElButton class="cta-btn" @click="router.push('/portal/doctors')">{{ t('auth.findADoctor') }}</ElButton>
        </div>
      </div>
    </section>

    <section class="login-form-area">
      <div class="login-card">
        <h2>{{ t('auth.welcomeBack') }}</h2>
        <p>{{ t('auth.signInToContinue') }}</p>

        <ElForm
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          class="login-form"
          @submit.prevent="login"
        >
          <ElFormItem :label="t('auth.usernameOrEmail')" prop="account">
            <ElInput
              v-model="form.account"
              size="large"
              autocomplete="username"
              :placeholder="t('auth.enterUsername')"
            />
          </ElFormItem>

          <ElFormItem :label="t('auth.password')" prop="password">
            <ElInput
              v-model="form.password"
              size="large"
              type="password"
              autocomplete="current-password"
              :placeholder="t('auth.enterPassword')"
              show-password
            />
          </ElFormItem>

          <ElFormItem class="login-submit-row">
            <ElButton
              type="primary"
              size="large"
              :loading="loading"
              native-type="submit"
              class="login-submit-btn"
            >
              {{ t('auth.signIn') }}
            </ElButton>
          </ElFormItem>
        </ElForm>
      </div>
    </section>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.05fr 1fr;
  background: #edf2f7;
}

.login-brand {
  position: relative;
  background: linear-gradient(150deg, #4f73ea 0%, #2e57db 60%, #1f3fb6 100%);
  color: #e9f0ff;
  padding: 56px 60px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  overflow: hidden;
  isolation: isolate;
}

.login-brand::before,
.login-brand::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  filter: blur(60px);
  z-index: -1;
}

.login-brand::before {
  width: 380px;
  height: 380px;
  top: -120px;
  right: -120px;
  background: rgba(132, 168, 255, 0.45);
}

.login-brand::after {
  width: 320px;
  height: 320px;
  bottom: -80px;
  left: -80px;
  background: rgba(35, 82, 200, 0.6);
}

.login-logo-wrap {
  display: inline-flex;
}

.login-hero {
  margin-top: auto;
  max-width: 480px;
}

.login-hero h1 {
  margin: 0;
  font-size: clamp(32px, 3.4vw, 48px);
  line-height: 1.1;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: #ffffff;
}

.login-hero p {
  margin: 18px 0 0;
  font-size: 15px;
  line-height: 1.6;
  color: rgba(232, 240, 255, 0.85);
  max-width: 420px;
}

.login-form-area {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 32px;
}

.login-card {
  width: 100%;
  max-width: 400px;
}

.login-card h2 {
  margin: 0;
  font-size: 30px;
  font-weight: 700;
  color: #1b2a4a;
  letter-spacing: -0.3px;
}

.login-card > p {
  margin: 8px 0 32px;
  font-size: 14px;
  color: #6f7894;
}

.login-form {
  display: grid;
  gap: 4px;
}

.login-form :deep(.el-form-item__label) {
  font-size: 13px;
  font-weight: 600;
  color: #2e3a59;
  padding: 0 0 6px;
  line-height: 1.3;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.login-form :deep(.el-input) {
  width: 100%;
  --el-input-bg-color: #f8fbff;
  --el-input-border-color: #cfd9ec;
  --el-input-hover-border-color: #b8c7e3;
  --el-input-focus-border-color: #3f67ea;
  --el-input-text-color: #1f2f4e;
  --el-input-placeholder-color: #95a3c2;
}

.login-form :deep(.el-input__wrapper) {
  background-color: #f8fbff;
  border-radius: 12px;
  padding: 0 14px;
  box-shadow: 0 0 0 1px #cfd9ec inset;
  transition: box-shadow 0.18s ease, background-color 0.18s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #b8c7e3 inset;
}

.login-form :deep(.el-input.is-focus .el-input__wrapper) {
  background-color: #ffffff;
  box-shadow: 0 0 0 1px #3f67ea inset, 0 0 0 3px rgba(63, 103, 234, 0.14);
}

.login-form :deep(.el-input__inner) {
  border: 0 !important;
  background: transparent !important;
  padding: 0 !important;
  height: 44px !important;
  min-height: 44px !important;
  font-size: 14px !important;
  color: #1f2f4e !important;
  box-shadow: none !important;
  border-radius: 0 !important;
}

.login-form :deep(.el-input__inner::placeholder) {
  color: #95a3c2;
}

.login-form :deep(.el-input__suffix) {
  color: #8895b6;
}

.login-form :deep(.el-form-item.is-error .el-input__wrapper) {
  box-shadow: 0 0 0 1px #d13b54 inset !important;
  background-color: #fff7f8 !important;
}

.login-form :deep(.el-form-item__error) {
  font-size: 12px;
  padding-top: 4px;
}

.login-submit-row {
  margin-top: 10px;
  margin-bottom: 0;
}

.login-submit-row :deep(.el-form-item__content) {
  width: 100%;
  line-height: 1;
}

.login-submit-btn {
  width: 100%;
  height: 48px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 15px;
  letter-spacing: 0.2px;
  border: 0;
  background: linear-gradient(135deg, #3e66e9 0%, #3058d9 100%);
  box-shadow: 0 10px 22px rgba(48, 88, 217, 0.22);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.login-submit-btn:hover {
  filter: brightness(1.04);
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(48, 88, 217, 0.3);
}

.login-submit-btn:active {
  transform: translateY(0);
  box-shadow: 0 6px 14px rgba(48, 88, 217, 0.22);
}

.login-portal-preview {
  margin-top: 40px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.login-portal-cta {
  display: flex;
  gap: 12px;
}
.cta-btn {
  background: rgba(255, 255, 255, 0.15);
  border: 1px solid rgba(255, 255, 255, 0.3);
  color: #fff;
  border-radius: 12px;
  padding: 10px 18px;
}
.cta-btn:hover {
  background: rgba(255, 255, 255, 0.25);
}

@media (max-width: 880px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .login-brand {
    padding: 36px 32px;
    min-height: 280px;
  }
  .login-hero {
    margin-top: 24px;
  }
  .login-form-area {
    padding: 36px 24px;
  }
  .login-portal-preview { margin-top: 20px; }
}
</style>
