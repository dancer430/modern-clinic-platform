<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import apiClient from '@/utils/apiClient'
import { useAuthStore } from '@/stores/auth'

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
  username: [{ required: true, message: 'Username is required', trigger: 'blur' }],
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
  email: [{ required: true, message: 'Email is required', trigger: 'blur' }],
  phone: [{ required: true, message: 'Phone is required', trigger: 'blur' }],
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
  const response = await apiClient.get('/api/auth/doctors/')
  doctors.value = response.data
}

const loadPageData = async () => {
  loading.value = true
  try {
    await fetchDoctors()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Failed to load doctors')
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
      await apiClient.patch(`/api/auth/doctors/${editingId.value}/`, payload)
    } else {
      await apiClient.post('/api/auth/doctors/', payload)
    }
    showDialog.value = false
    ElMessage.success(editingId.value ? 'Doctor updated' : 'Doctor created')
    await fetchDoctors()
  } catch (error: any) {
    ElMessage.error(extractErrorMessage(error, 'Save doctor failed'))
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
    await apiClient.delete(`/api/auth/doctors/${deleteTarget.value.id}/`)
    showDeleteDialog.value = false
    deleteTarget.value = null
    ElMessage.success('Doctor deleted')
    await fetchDoctors()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Delete doctor failed')
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
        <h2>Doctors</h2>
        <p>{{ filteredDoctors.length }} doctor accounts</p>
      </div>
      <el-button type="primary" :disabled="!canManage" @click="openCreate">+ Add Doctor</el-button>
    </section>

    <el-alert
      v-if="!canManage"
      title="Only admin can create, edit, or delete doctor accounts."
      type="warning"
      show-icon
      :closable="false"
      style="margin-bottom: 16px"
    />

    <section class="toolbar" style="gap: 12px">
      <el-input
        v-model="query"
        placeholder="Search doctor account"
        clearable
        style="max-width: 320px"
      />
      <el-select v-model="statusFilter" style="width: 160px">
        <el-option label="All status" value="all" />
        <el-option label="Active" value="active" />
        <el-option label="Inactive" value="inactive" />
      </el-select>
    </section>

    <el-table
      v-loading="loading"
      :data="filteredDoctors"
      stripe
      style="width: 100%; margin-top: 16px"
    >
      <el-table-column prop="name" label="Name" min-width="140">
        <template #default="{ row }">{{ displayName(row) }}</template>
      </el-table-column>
      <el-table-column prop="email" label="Email" min-width="180">
        <template #default="{ row }">{{ row.email || '-' }}</template>
      </el-table-column>
      <el-table-column prop="phone" label="Phone" min-width="130">
        <template #default="{ row }">{{ row.phone || '-' }}</template>
      </el-table-column>
      <el-table-column label="Status" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
            {{ row.is_active ? 'active' : 'inactive' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Actions" width="180" fixed="right">
        <template #default="{ row }">
          <el-button text :disabled="!canManage" @click="openEdit(row)">Edit</el-button>
          <el-button text type="danger" :disabled="!canManage" @click="requestRemoveDoctor(row)">Delete</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="No doctors found" />
      </template>
    </el-table>

    <!-- Delete confirmation dialog -->
    <el-dialog
      v-model="showDeleteDialog"
      title="Delete Doctor Account"
      width="460px"
      :before-close="() => closeDeleteDialog()"
    >
      <p>
        You are about to delete <strong>{{ deleteTarget ? displayName(deleteTarget) : '-' }}</strong>. This action cannot be undone.
      </p>
      <template #footer>
        <el-button @click="closeDeleteDialog">Keep Account</el-button>
        <el-button type="danger" @click="removeDoctor">Delete Permanently</el-button>
      </template>
    </el-dialog>

    <!-- Create / Edit dialog -->
    <el-dialog
      v-model="showDialog"
      :title="editingId ? 'Edit Doctor' : 'Add Doctor'"
      width="560px"
      @close="onDialogClose"
    >
      <el-form ref="formRef" :model="form" :rules="formRules" label-position="top">
        <el-form-item label="Username" prop="username">
          <el-input v-model="form.username" placeholder="Username" />
        </el-form-item>
        <el-form-item label="Name" prop="name">
          <el-input v-model="form.name" placeholder="Name" />
        </el-form-item>
        <el-form-item label="Email" prop="email">
          <el-input v-model="form.email" placeholder="Email" />
        </el-form-item>
        <el-form-item label="Phone" prop="phone">
          <el-input v-model="form.phone" placeholder="Phone" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            :placeholder="editingId ? 'Reset password (optional)' : 'Initial password (optional)'"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showDialog = false">Cancel</el-button>
        <el-button type="primary" @click="saveDoctor">Save</el-button>
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
