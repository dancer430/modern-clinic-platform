<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import apiClient from '@/utils/axios'
import { useAuthStore } from '@/stores/auth'
import { usePlatformBrand } from '@/composables/usePlatformBrand'

const authStore = useAuthStore()
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const avatarInputRef = ref<HTMLInputElement | null>(null)
const avatarUploaderDragging = ref(false)
const passwordSubmitAttempted = ref(false)
const platformLogoInputRef = ref<HTMLInputElement | null>(null)
const platformLogoDragging = ref(false)

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
      label: 'Not set',
      percent: 0,
      tone: 'none',
    }
  }

  let score = 0
  if (password.length >= 8) score += 1
  if (/[A-Z]/.test(password) && /[a-z]/.test(password)) score += 1
  if (/\d/.test(password)) score += 1
  if (/[^A-Za-z0-9]/.test(password)) score += 1

  if (score <= 1) return { score, label: 'Weak', percent: 25, tone: 'weak' }
  if (score === 2) return { score, label: 'Medium', percent: 50, tone: 'medium' }
  if (score === 3) return { score, label: 'Strong', percent: 75, tone: 'strong' }
  return { score, label: 'Very strong', percent: 100, tone: 'very-strong' }
})

const displayName = computed(() => {
  return profileForm.value.name.trim() || authStore.user?.username || 'User'
})

const isAdmin = computed(() => authStore.isAdmin)

const loadProfile = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await apiClient.get('/me/')
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
    errorMessage.value = error.response?.data?.detail || 'Failed to load profile'
  } finally {
    loading.value = false
  }
}

const loadPlatform = async () => {
  try {
    const response = await apiClient.get('/platform/')
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

const onAvatarChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  await processAvatarFile(file)
  input.value = ''
}

const processAvatarFile = async (file: File) => {
  const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg']
  if (!allowedTypes.includes(file.type)) {
    errorMessage.value = 'Avatar must be PNG or JPG'
    return
  }

  const sizeKB = Math.ceil(file.size / 1024)
  if (sizeKB > 1024) {
    errorMessage.value = 'Avatar size must be <= 1MB'
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

const openAvatarPicker = () => {
  avatarInputRef.value?.click()
}

const onAvatarUploaderDrop = async (event: DragEvent) => {
  avatarUploaderDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (!file) return
  try {
    await processAvatarFile(file)
  } catch {
    errorMessage.value = 'Failed to read avatar file'
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
    errorMessage.value = 'Platform logo must be PNG or JPG'
    return
  }

  const sizeKB = Math.ceil(file.size / 1024)
  if (sizeKB > 1024) {
    errorMessage.value = 'Platform logo size must be <= 1MB'
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

const onPlatformLogoChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  await processPlatformLogoFile(file)
  input.value = ''
}

const openPlatformLogoPicker = () => {
  platformLogoInputRef.value?.click()
}

const onPlatformLogoDrop = async (event: DragEvent) => {
  platformLogoDragging.value = false
  const file = event.dataTransfer?.files?.[0]
  if (!file) return
  await processPlatformLogoFile(file)
}

const removePlatformLogo = () => {
  platformForm.value.logo_data = ''
  platformForm.value.logo_type = ''
  platformForm.value.logo_size = null
}

const savePlatform = async () => {
  if (!isAdmin.value) return
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await apiClient.patch('/platform/', platformForm.value)
    await loadPlatformBrand(true)
    successMessage.value = 'Platform branding updated successfully'
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to update platform branding'
  }
}

const saveProfile = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const response = await apiClient.patch('/me/', profileForm.value)
    authStore.setUser(response.data)
    successMessage.value = 'Profile updated successfully'
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to update profile'
  }
}

const changePassword = async () => {
  errorMessage.value = ''
  successMessage.value = ''
  passwordSubmitAttempted.value = true

  if (!passwordForm.value.current_password || !passwordForm.value.new_password || !passwordForm.value.confirm_password) {
    errorMessage.value = 'Please complete all password fields'
    return
  }

  try {
    await apiClient.post('/change-password/', passwordForm.value)
    passwordForm.value = {
      current_password: '',
      new_password: '',
      confirm_password: '',
    }
    passwordSubmitAttempted.value = false
    successMessage.value = 'Password updated successfully'
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to update password'
  }
}

onMounted(async () => {
  await Promise.all([loadProfile(), loadPlatform()])
})
</script>

<template>
  <div class="page profile-page">
    <section class="toolbar">
      <div>
        <h2>Personal Center</h2>
        <p>Manage your contact details, avatar, and password.</p>
      </div>
    </section>

    <section v-if="errorMessage" class="table-card" style="padding: 10px 12px; color: #c2334a;">
      {{ errorMessage }}
    </section>
    <section v-if="successMessage" class="table-card" style="padding: 10px 12px; color: #22815c;">
      {{ successMessage }}
    </section>

    <section class="profile-grid">
      <article class="table-card profile-card">
        <h3>Profile</h3>
        <div class="profile-avatar-row">
          <div class="profile-avatar-preview">
            <img v-if="profileForm.avatar_data" :src="profileForm.avatar_data" alt="avatar" />
            <span v-else>{{ displayName[0] }}</span>
          </div>
          <div class="profile-avatar-actions">
              <div
                class="file-uploader"
                :class="{ dragging: avatarUploaderDragging }"
                role="button"
                tabindex="0"
                @click="openAvatarPicker"
                @keydown.enter.prevent="openAvatarPicker"
                @dragover.prevent="avatarUploaderDragging = true"
                @dragleave.prevent="avatarUploaderDragging = false"
                @drop.prevent="onAvatarUploaderDrop"
              >
                <input
                  ref="avatarInputRef"
                  type="file"
                  accept="image/png,image/jpeg"
                  class="hidden-file-input"
                  @change="onAvatarChange"
                />
                <span class="file-uploader-icon">⬆</span>
                <div>
                  <p class="file-uploader-title">Upload avatar</p>
                  <p class="file-uploader-subtitle">PNG or JPG, up to 1MB. Drag and drop supported.</p>
                </div>
              </div>
            <button class="ghost" @click="removeAvatar">Remove avatar</button>
          </div>
        </div>

        <div class="grid">
          <input v-model="profileForm.name" placeholder="Name" />
          <input v-model="profileForm.email" placeholder="Email" />
          <input v-model="profileForm.phone" placeholder="Phone" />
        </div>

        <div class="actions">
          <button class="primary" :disabled="loading" @click="saveProfile">Save Profile</button>
        </div>
      </article>

      <article class="table-card profile-card password-card">
        <h3>Change Password</h3>
        <p class="password-card-tip">Use a strong password and keep your account secure.</p>
        <div class="profile-password-form">
          <label class="field-label">Current Password <span class="required-mark">*</span></label>
          <input
            v-model="passwordForm.current_password"
            type="password"
            placeholder="Enter current password"
            :class="{ 'input-invalid': passwordSubmitAttempted && !passwordForm.current_password }"
          />

          <label class="field-label">New Password <span class="required-mark">*</span></label>
          <input
            v-model="passwordForm.new_password"
            type="password"
            placeholder="Enter new password"
            :class="{ 'input-invalid': passwordSubmitAttempted && !passwordForm.new_password }"
          />
          <div class="password-strength-wrap">
            <div class="password-strength-track">
              <div
                class="password-strength-fill"
                :class="`tone-${passwordStrength.tone}`"
                :style="{ width: `${passwordStrength.percent}%` }"
              ></div>
            </div>
            <span class="password-strength-text" :class="`tone-${passwordStrength.tone}`">
              Strength: {{ passwordStrength.label }}
            </span>
          </div>

          <label class="field-label">Confirm New Password <span class="required-mark">*</span></label>
          <input
            v-model="passwordForm.confirm_password"
            type="password"
            placeholder="Re-enter new password"
            :class="{ 'input-invalid': passwordSubmitAttempted && !passwordForm.confirm_password }"
          />
        </div>
        <div class="actions">
          <button class="primary" @click="changePassword">Update Password</button>
        </div>
      </article>

      <article v-if="isAdmin" class="table-card profile-card">
        <h3>Platform Branding</h3>
        <p class="password-card-tip">Admin-only: customize platform name and logo shown in login and sidebar.</p>
        <div class="profile-avatar-row">
          <div class="profile-avatar-preview">
            <img v-if="platformForm.logo_data" :src="platformForm.logo_data" alt="platform logo" />
            <span v-else>P</span>
          </div>
          <div class="profile-avatar-actions">
            <div
              class="file-uploader"
              :class="{ dragging: platformLogoDragging }"
              role="button"
              tabindex="0"
              @click="openPlatformLogoPicker"
              @keydown.enter.prevent="openPlatformLogoPicker"
              @dragover.prevent="platformLogoDragging = true"
              @dragleave.prevent="platformLogoDragging = false"
              @drop.prevent="onPlatformLogoDrop"
            >
              <input
                ref="platformLogoInputRef"
                type="file"
                accept="image/png,image/jpeg"
                class="hidden-file-input"
                @change="onPlatformLogoChange"
              />
              <span class="file-uploader-icon">⬆</span>
              <div>
                <p class="file-uploader-title">Upload platform logo</p>
                <p class="file-uploader-subtitle">PNG or JPG, up to 1MB. Drag and drop supported.</p>
              </div>
            </div>
            <button class="ghost" @click="removePlatformLogo">Remove logo</button>
          </div>
        </div>

        <div class="grid">
          <input v-model="platformForm.platform_name" placeholder="Platform name" />
        </div>

        <div class="actions">
          <button class="primary" @click="savePlatform">Save Branding</button>
        </div>
      </article>
    </section>
  </div>
</template>
