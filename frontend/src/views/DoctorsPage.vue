<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import httpClient from '@/shared/http'
import { useAuthStore } from '@/features/auth'

const { t } = useI18n()

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

const authStore = useAuthStore()
const loading = ref(false)
const doctors = ref<DoctorUser[]>([])

const query = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const showDeleteDialog = ref(false)
const deleteTarget = ref<DoctorUser | null>(null)
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

const filteredDoctors = computed(() => {
  return doctors.value.filter((item) => {
    const text = `${item.username} ${item.name} ${item.email} ${item.phone}`.toLowerCase()
    const hitSearch = !query.value || text.includes(query.value.toLowerCase())
    const hitStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'active' && item.is_active) ||
      (statusFilter.value === 'inactive' && !item.is_active)
    return hitSearch && hitStatus
  })
})

const displayName = (doctor: DoctorUser) => {
  return doctor.name?.trim() || '-'
}

const fetchDoctors = async () => {
  const response = await httpClient.get('/api/auth/doctors/')
  doctors.value = response.data
}

const loadPageData = async () => {
  loading.value = true
  try {
    await fetchDoctors()
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
  editingId.value = null
  resetForm()
  showDialog.value = true
}

const openEdit = (doctor: DoctorUser) => {
  if (!canManage.value) return
  editingId.value = doctor.id
  form.value = {
    username: doctor.username,
    name: doctor.name,
    email: doctor.email,
    phone: doctor.phone,
    password: '',
  }
  showDialog.value = true
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
    if (editingId.value) {
      await httpClient.patch(`/api/auth/doctors/${editingId.value}/`, payload)
    } else {
      await httpClient.post('/api/auth/doctors/', payload)
    }
    showDialog.value = false
    ElMessage.success(editingId.value ? t('doctors.updated') : t('doctors.created'))
    await fetchDoctors()
  } catch (error: any) {
    ElMessage.error(extractErrorMessage(error, t('doctors.saveFailed')))
  }
}

const requestRemoveDoctor = (doctor: DoctorUser) => {
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
    await fetchDoctors()
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
      <el-select v-model="statusFilter" style="width: 160px">
        <el-option :label="t('doctors.allStatus')" value="all" />
        <el-option :label="t('doctors.statusActive')" value="active" />
        <el-option :label="t('doctors.statusInactive')" value="inactive" />
      </el-select>
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
      <el-table-column prop="email" :label="t('doctors.columnEmail')" min-width="180">
        <template #default="{ row }">{{ row.email || '-' }}</template>
      </el-table-column>
      <el-table-column prop="phone" :label="t('doctors.columnPhone')" min-width="130">
        <template #default="{ row }">{{ row.phone || '-' }}</template>
      </el-table-column>
      <el-table-column :label="t('doctors.columnStatus')" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? t('doctors.tagActive') : t('doctors.tagInactive') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="t('common.actions')" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text :disabled="!canManage" @click="openEdit(row)">{{ t('common.edit') }}</el-button>
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

    <!-- Create / Edit dialog -->
    <el-dialog
      v-model="showDialog"
      :title="editingId ? t('doctors.editTitle') : t('doctors.addTitle')"
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
            :placeholder="editingId ? t('doctors.placeholderResetPassword') : t('doctors.placeholderInitialPassword')"
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
