<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import httpClient from '@/shared/http'
import { useAuthStore } from '@/features/auth'
import { usePlatformBrand } from '@/composables/usePlatformBrand'

const { t } = useI18n()

const authStore = useAuthStore()
const loading = ref(false)
const avatarUploadRef = ref()
const platformLogoUploadRef = ref()
const passwordSubmitAttempted = ref(false)

const { loadPlatformBrand } = usePlatformBrand()

const profileForm = ref({
  name: '',
  email: '',
  phone: '',
  avatar_data: '',
  avatar_type: '',
  avatar_size: null as number | null,
})

const passwordForm = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
})

const platformForm = ref({
  platform_name: '',
  logo_data: '',
  logo_type: '',
  logo_size: null as number | null,
})

const passwordStrength = computed(() => {
  const password = passwordForm.value.new_password
  if (!password) {
    return {
      score: 0,
      label: t('profile.strengthNotSet'),
      percent: 0,
      tone: 'none',
    }
  }

  let score = 0
  if (password.length >= 8) score += 1
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1
  if (/\d/.test(password)) score += 1
  if (/[^A-Za-z0-9]/.test(password)) score += 1

  if (score <= 1) return { score, label: t('profile.strengthWeak'), percent: 25, tone: 'weak' }
  if (score === 2) return { score, label: t('profile.strengthMedium'), percent: 50, tone: 'medium' }
  if (score === 3) return { score, label: t('profile.strengthStrong'), percent: 75, tone: 'strong' }
  return { score, label: t('profile.strengthVeryStrong'), percent: 100, tone: 'very-strong' }
})

const strengthColor = computed(() => {
  const tone = passwordStrength.value.tone
  if (tone === 'weak') return '#F56C6C'
  if (tone === 'medium') return '#E6A23C'
  if (tone === 'strong') return '#409EFF'
  if (tone === 'very-strong') return '#67C23A'
  return '#C0C4CC'
})

const displayName = computed(() => {
  return profileForm.value.name.trim() || authStore.user?.username || t('profile.defaultUser')
})

const isAdmin = computed(() => authStore.isAdmin)

const loadProfile = async () => {
  loading.value = true
  try {
    const response = await httpClient.get('/api/auth/me/')
    const user = response.data
    authStore.setUser(user)
    profileForm.value = {
      name: user.name || '',
      email: user.email || '',
      phone: user.phone || '',
      avatar_data: user.avatar_data || '',
      avatar_type: user.avatar_type || '',
      avatar_size: user.avatar_size ?? null,
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('profile.profileLoadFailed'))
  } finally {
    loading.value = false
  }
}

const loadPlatform = async () => {
  try {
    const response = await httpClient.get('/api/auth/platform/')
    const data = response.data
    platformForm.value = {
      platform_name: data.platform_name || '',
      logo_data: data.logo_data || '',
      logo_type: data.logo_type || '',
      logo_size: data.logo_size ?? null,
    }
  } catch {
    // non-blocking
  }
}

const processAvatarFile = async (file: File) => {
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error(t('profile.avatarMustBeImage'))
    return
  }

  const sizeKB = Math.ceil(file.size / 1024)
  if (sizeKB > 1024) {
    ElMessage.error(t('profile.avatarTooLarge'))
    return
  }

  const base64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve((reader.result as string) || '')
    reader.onerror = () => reject(new Error('Failed to read avatar file'))
    reader.readAsDataURL(file)
  })

  profileForm.value.avatar_data = base64
  profileForm.value.avatar_type = file.type
  profileForm.value.avatar_size = sizeKB
}

const onAvatarUploadChange = async (uploadFile: UploadFile) => {
  if (uploadFile.raw) {
    await processAvatarFile(uploadFile.raw)
  }
  // Clear the upload file list so the slot stays clean
  if (avatarUploadRef.value) {
    avatarUploadRef.value.clearFiles()
  }
}

const removeAvatar = () => {
  profileForm.value.avatar_data = ''
  profileForm.value.avatar_type = ''
  profileForm.value.avatar_size = null
}

const processPlatformLogoFile = async (file: File) => {
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg']
  if (!allowedTypes.includes(file.type)) {
    ElMessage.error(t('profile.logoMustBeImage'))
    return
  }

  const sizeKB = Math.ceil(file.size / 1024)
  if (sizeKB > 1024) {
    ElMessage.error(t('profile.logoTooLarge'))
    return
  }

  const base64 = await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve((reader.result as string) || '')
    reader.onerror = () => reject(new Error('Failed to read logo file'))
    reader.readAsDataURL(file)
  })

  platformForm.value.logo_data = base64
  platformForm.value.logo_type = file.type
  platformForm.value.logo_size = sizeKB
}

const onPlatformLogoUploadChange = async (uploadFile: UploadFile) => {
  if (uploadFile.raw) {
    await processPlatformLogoFile(uploadFile.raw)
  }
  if (platformLogoUploadRef.value) {
    platformLogoUploadRef.value.clearFiles()
  }
}

const removePlatformLogo = () => {
  platformForm.value.logo_data = ''
  platformForm.value.logo_type = ''
  platformForm.value.logo_size = null
}

const savePlatform = async () => {
  if (!isAdmin.value) return
  try {
    await httpClient.patch('/api/auth/platform/', platformForm.value)
    await loadPlatformBrand(true)
    ElMessage.success(t('profile.brandingUpdated'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('profile.brandingUpdateFailed'))
  }
}

const saveProfile = async () => {
  try {
    const response = await httpClient.patch('/api/auth/me/', profileForm.value)
    authStore.setUser(response.data)
    ElMessage.success(t('profile.profileUpdated'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('profile.profileUpdateFailed'))
  }
}

const changePassword = async () => {
  passwordSubmitAttempted.value = true

  if (!passwordForm.value.current_password || !passwordForm.value.new_password || !passwordForm.value.confirm_password) {
    ElMessage.error(t('profile.completeAllPasswordFields'))
    return
  }

  try {
    await httpClient.post('/api/auth/change-password/', passwordForm.value)
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: '',
    }
    passwordSubmitAttempted.value = false
    ElMessage.success(t('profile.passwordUpdated'))
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('profile.passwordUpdateFailed'))
  }
}

onMounted(async () => {
  await Promise.all([loadProfile(), loadPlatform()])
})
</script>

<template>
  <div class="page profile-page" v-loading="loading">
    <section class="toolbar">
      <div>
        <h2>{{ t('profile.title') }}</h2>
        <p>{{ t('profile.subtitle') }}</p>
      </div>
    </section>

    <section class="profile-grid">
      <el-card shadow="never">
        <template #header>
          <span>{{ t('profile.profileCard') }}</span>
        </template>

        <div class="profile-avatar-row">
          <div class="profile-avatar-preview">
            <img v-if="profileForm.avatar_data" :src="profileForm.avatar_data" alt="avatar" />
            <span v-else>{{ displayName[0] }}</span>
          </div>
          <div class="profile-avatar-actions">
            <el-upload
              ref="avatarUploadRef"
              :auto-upload="false"
              :on-change="onAvatarUploadChange"
              accept="image/png,image/jpeg"
              :limit="1"
              :show-file-list="false"
              list-type="picture-card"
            >
              <div class="upload-trigger">
                <el-icon><Plus /></el-icon>
                <span>{{ t('profile.uploadAvatar') }}</span>
              </div>
            </el-upload>
            <el-button text @click="removeAvatar">{{ t('profile.removeAvatar') }}</el-button>
          </div>
        </div>

        <el-form label-position="top">
          <el-form-item :label="t('profile.fieldName')">
            <el-input v-model="profileForm.name" :placeholder="t('profile.placeholderName')" />
          </el-form-item>
          <el-form-item :label="t('profile.fieldEmail')">
            <el-input v-model="profileForm.email" :placeholder="t('profile.placeholderEmail')" />
          </el-form-item>
          <el-form-item :label="t('profile.fieldPhone')">
            <el-input v-model="profileForm.phone" :placeholder="t('profile.placeholderPhone')" />
          </el-form-item>
        </el-form>

        <div class="actions">
          <el-button type="primary" :disabled="loading" @click="saveProfile">{{ t('profile.saveProfile') }}</el-button>
        </div>
      </el-card>

      <el-card shadow="never">
        <template #header>
          <span>{{ t('profile.changePassword') }}</span>
        </template>

        <p class="password-card-tip">{{ t('profile.passwordTip') }}</p>

        <el-form label-position="top">
          <el-form-item :label="t('profile.currentPassword')" required>
            <el-input
              v-model="passwordForm.current_password"
              type="password"
              show-password
              :placeholder="t('profile.enterCurrentPassword')"
              :class="{ 'is-error': passwordSubmitAttempted && !passwordForm.current_password }"
            />
          </el-form-item>

          <el-form-item :label="t('profile.newPassword')" required>
            <el-input
              v-model="passwordForm.new_password"
              type="password"
              show-password
              :placeholder="t('profile.enterNewPassword')"
              :class="{ 'is-error': passwordSubmitAttempted && !passwordForm.new_password }"
            />
          </el-form-item>

          <div class="password-strength-wrap">
            <el-progress
              :percentage="passwordStrength.percent"
              :color="strengthColor"
              :stroke-width="8"
              :show-text="false"
              striped
            />
            <span class="password-strength-text">{{ t('profile.strengthPrefix') }} {{ passwordStrength.label }}</span>
          </div>

          <el-form-item :label="t('profile.confirmNewPassword')" required>
            <el-input
              v-model="passwordForm.confirm_password"
              type="password"
              show-password
              :placeholder="t('profile.reenterNewPassword')"
              :class="{ 'is-error': passwordSubmitAttempted && !passwordForm.confirm_password }"
            />
          </el-form-item>
        </el-form>

        <div class="actions">
          <el-button type="primary" @click="changePassword">{{ t('profile.updatePassword') }}</el-button>
        </div>
      </el-card>

      <el-card v-if="isAdmin" shadow="never">
        <template #header>
          <span>{{ t('profile.platformBranding') }}</span>
        </template>

        <p class="password-card-tip">{{ t('profile.platformBrandingTip') }}</p>

        <div class="profile-avatar-row">
          <div class="profile-avatar-preview">
            <img v-if="platformForm.logo_data" :src="platformForm.logo_data" alt="platform logo" />
            <span v-else>P</span>
          </div>
          <div class="profile-avatar-actions">
            <el-upload
              ref="platformLogoUploadRef"
              :auto-upload="false"
              :on-change="onPlatformLogoUploadChange"
              accept="image/png,image/jpeg"
              :limit="1"
              :show-file-list="false"
              list-type="picture-card"
            >
              <div class="upload-trigger">
                <el-icon><Plus /></el-icon>
                <span>{{ t('profile.uploadPlatformLogo') }}</span>
              </div>
            </el-upload>
            <el-button text @click="removePlatformLogo">{{ t('profile.removeLogo') }}</el-button>
          </div>
        </div>

        <el-form label-position="top">
          <el-form-item :label="t('profile.platformName')">
            <el-input v-model="platformForm.platform_name" :placeholder="t('profile.placeholderPlatformName')" />
          </el-form-item>
        </el-form>

        <div class="actions">
          <el-button type="primary" @click="savePlatform">{{ t('profile.saveBranding') }}</el-button>
        </div>
      </el-card>
    </section>
  </div>
</template>

<style scoped>
.password-strength-wrap {
  margin-bottom: 18px;
}

.password-strength-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
  display: inline-block;
}

.password-card-tip {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}

.upload-trigger {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
