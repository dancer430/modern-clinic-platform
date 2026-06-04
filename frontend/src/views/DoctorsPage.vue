<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import httpClient from '@/shared/http'
import { useAuthStore } from '@/features/auth'
import { adminDoctorProfilesApi } from '@/features/content/api/doctor-profiles'
import type { DoctorProfileAdmin } from '@/features/content/types'

const { t } = useI18n()
const router = useRouter()

interface DoctorUser {
  id: number
  username: string
  email: string
  name: string
  role: 'doctor'
  user_type: 'doctor'
  phone: string
  is_active: boolean
}

type ProfileStatus = 'published' | 'pending' | 'draft' | 'rejected' | 'none'

interface DoctorRow extends DoctorUser {
  profile?: DoctorProfileAdmin
  title: string
  specialty: string
  departmentNames: string
  profileStatus: ProfileStatus
}

function deriveStatus(p?: DoctorProfileAdmin): ProfileStatus {
  if (!p) return 'none'
  if (p.draft_status === 'pending') return 'pending'
  if (p.is_published) return 'published'
  if (p.draft_status === 'rejected') return 'rejected'
  return p.title || p.specialty ? 'draft' : 'none'
}

const statusTagType: Record<ProfileStatus, 'success' | 'warning' | 'info' | 'danger'> = {
  published: 'success',
  pending: 'warning',
  draft: 'info',
  rejected: 'danger',
  none: 'info',
}

const authStore = useAuthStore()
const loading = ref(false)
const doctors = ref<DoctorUser[]>([])
const profiles = ref<DoctorProfileAdmin[]>([])

const query = ref('')
const reviewFilter = ref<'all' | 'pending'>('all')
const showDialog = ref(false)
const showDeleteDialog = ref(false)
const deleteTarget = ref<DoctorRow | null>(null)
const formRef = ref<FormInstance>()

const form = ref({
  username: '',
  name: '',
  email: '',
  phone: '',
  password: '',
})

const formRules: FormRules = {
  username: [{ required: true, message: () => t('doctors.usernameRequired'), trigger: 'blur' }],
  name: [{ required: true, message: () => t('doctors.nameRequired'), trigger: 'blur' }],
  email: [{ required: true, message: () => t('doctors.emailRequired'), trigger: 'blur' }],
  phone: [{ required: true, message: () => t('doctors.phoneRequired'), trigger: 'blur' }],
}

const canManage = computed(() => authStore.isAdmin)

const rows = computed<DoctorRow[]>(() => {
  const byUserId = new Map<number, DoctorProfileAdmin>()
  for (const p of profiles.value) byUserId.set(p.user_id, p)

  return doctors.value.map((doctor) => {
    const profile = byUserId.get(doctor.id)
    return {
      ...doctor,
      profile,
      title: profile?.title || '',
      specialty: profile?.specialty || '',
      departmentNames: profile?.departments?.map((d) => d.name).join(', ') || '',
      profileStatus: deriveStatus(profile),
    }
  })
})

const pendingCount = computed(
  () => rows.value.filter((row) => row.profileStatus === 'pending').length,
)

const filteredDoctors = computed(() => {
  return rows.value.filter((item) => {
    const text =
      `${item.username} ${item.name} ${item.email} ${item.phone} ${item.title} ${item.specialty} ${item.departmentNames}`.toLowerCase()
    const hitSearch = !query.value || text.includes(query.value.toLowerCase())
    const hitFilter = reviewFilter.value === 'all' || item.profileStatus === 'pending'
    return hitSearch && hitFilter
  })
})

const displayName = (doctor: DoctorRow | DoctorUser) => {
  return doctor.name?.trim() || '-'
}

const fetchData = async () => {
  const [doctorsRes, profilesRes] = await Promise.all([
    httpClient.get('/api/auth/doctors/'),
    adminDoctorProfilesApi.list(),
  ])
  doctors.value = doctorsRes.data
  profiles.value = profilesRes
}

const loadPageData = async () => {
  loading.value = true
  try {
    await fetchData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('doctors.loadFailed'))
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    username: '',
    name: '',
    email: '',
    phone: '',
    password: '',
  }
}

const openCreate = () => {
  if (!canManage.value) return
  resetForm()
  showDialog.value = true
}

const openDetail = (doctor: DoctorRow) => {
  router.push(`/doctors/${doctor.id}`)
}

const extractErrorMessage = (error: any, fallback: string) => {
  const data = error.response?.data
  if (typeof data?.detail === 'string') return data.detail
  if (typeof data === 'string') return data
  if (data && typeof data === 'object') {
    const firstKey = Object.keys(data)[0]
    const value = (data as Record<string, unknown>)[firstKey]
    if (Array.isArray(value) && value.length > 0) {
      return `${firstKey}: ${String(value[0])}`
    }
    if (typeof value === 'string') {
      return `${firstKey}: ${value}`
    }
  }
  return fallback
}

const saveDoctor = async () => {
  if (!canManage.value) return
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  const payload = {
    username: form.value.username.trim(),
    name: form.value.name.trim(),
    email: form.value.email.trim(),
    phone: form.value.phone.trim(),
    ...(form.value.password.trim() ? { password: form.value.password.trim() } : {}),
  }

  try {
    await httpClient.post('/api/auth/doctors/', payload)
    showDialog.value = false
    ElMessage.success(t('doctors.created'))
    await fetchData()
  } catch (error: any) {
    ElMessage.error(extractErrorMessage(error, t('doctors.saveFailed')))
  }
}

const requestRemoveDoctor = (doctor: DoctorRow) => {
  if (!canManage.value) return
  deleteTarget.value = doctor
  showDeleteDialog.value = true
}

const closeDeleteDialog = () => {
  showDeleteDialog.value = false
  deleteTarget.value = null
}

const removeDoctor = async () => {
  if (!canManage.value) return
  if (!deleteTarget.value) return
  try {
    await httpClient.delete(`/api/auth/doctors/${deleteTarget.value.id}/`)
    showDeleteDialog.value = false
    deleteTarget.value = null
    ElMessage.success(t('doctors.deleted'))
    await fetchData()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('doctors.deleteFailed'))
  }
}

const onDialogClose = () => {
  formRef.value?.resetFields()
}

onMounted(async () => {
  await loadPageData()
})
</script>

<template>
  <div class="page">
    <section class="toolbar">
      <div>
        <h2>{{ t('doctors.title') }}</h2>
        <p>{{ t('doctors.countSummary', { count: filteredDoctors.length }) }}</p>
      </div>
      <el-button type="primary" :disabled="!canManage" @click="openCreate">{{ t('doctors.addDoctor') }}</el-button>
    </section>

    <el-alert
      v-if="!canManage"
      :title="t('doctors.adminOnlyNotice')"
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
    />

    <section class="toolbar" style="gap: 12px">
      <el-input
        v-model="query"
        :placeholder="t('doctors.searchPlaceholder')"
        clearable
        style="max-width: 320px"
      />
      <el-radio-group v-model="reviewFilter">
        <el-radio-button value="all">{{ t('doctors.filterAll') }}</el-radio-button>
        <el-radio-button value="pending">
          {{ t('doctors.filterPending') }} {{ pendingCount }}
        </el-radio-button>
      </el-radio-group>
    </section>

    <el-table
      v-loading="loading"
      :data="filteredDoctors"
      stripe
      style="width: 100%; margin-top: 16px"
    >
      <el-table-column prop="name" :label="t('doctors.columnName')" min-width="140">
        <template #default="{ row }">{{ displayName(row) }}</template>
      </el-table-column>
      <el-table-column prop="title" :label="t('doctors.columnTitle')" min-width="120">
        <template #default="{ row }">{{ row.title || '-' }}</template>
      </el-table-column>
      <el-table-column prop="specialty" :label="t('doctors.columnSpecialty')" min-width="160">
        <template #default="{ row }">{{ row.specialty || '-' }}</template>
      </el-table-column>
      <el-table-column :label="t('doctors.columnDepartments')" min-width="160">
        <template #default="{ row }">{{ row.departmentNames || '-' }}</template>
      </el-table-column>
      <el-table-column :label="t('doctors.columnProfileStatus')" width="130">
        <template #default="{ row }">
          <el-tag :type="statusTagType[row.profileStatus]" size="small">
            {{ t('doctorStatus.' + row.profileStatus) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.actions')" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text @click="openDetail(row)">{{ t('common.edit') }}</el-button>
          <el-button text type="danger" :disabled="!canManage" @click="requestRemoveDoctor(row)">{{ t('common.delete') }}</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty :description="t('doctors.empty')" />
      </template>
    </el-table>

    <!-- Delete confirmation dialog -->
    <el-dialog
      v-model="showDeleteDialog"
      :title="t('doctors.deleteTitle')"
      width="460px"
      :before-close="() => closeDeleteDialog()"
    >
      <p>
        {{ t('doctors.deleteConfirmPrefix') }} <strong>{{ deleteTarget ? displayName(deleteTarget) : '-' }}</strong>{{ t('doctors.deleteConfirmSuffix') }}
      </p>
      <template #footer>
        <el-button @click="closeDeleteDialog">{{ t('doctors.keepAccount') }}</el-button>
        <el-button type="danger" @click="removeDoctor">{{ t('doctors.deletePermanently') }}</el-button>
      </template>
    </el-dialog>

    <!-- Create dialog (account creation) -->
    <el-dialog
      v-model="showDialog"
      :title="t('doctors.addTitle')"
      width="560px"
      @close="onDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-position="top">
        <el-form-item :label="t('doctors.fieldUsername')" prop="username">
          <el-input v-model="form.username" :placeholder="t('doctors.placeholderUsername')" />
        </el-form-item>
        <el-form-item :label="t('doctors.fieldName')" prop="name">
          <el-input v-model="form.name" :placeholder="t('doctors.placeholderName')" />
        </el-form-item>
        <el-form-item :label="t('doctors.fieldEmail')" prop="email">
          <el-input v-model="form.email" :placeholder="t('doctors.placeholderEmail')" />
        </el-form-item>
        <el-form-item :label="t('doctors.fieldPhone')" prop="phone">
          <el-input v-model="form.phone" :placeholder="t('doctors.placeholderPhone')" />
        </el-form-item>
        <el-form-item :label="t('doctors.fieldPassword')">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="t('doctors.placeholderInitialPassword')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveDoctor">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
</style>
