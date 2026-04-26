<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import httpClient from '@/shared/http'
import { useAuthStore } from '@/features/auth'

interface PatientUser {
  id: number
  username: string
  email: string
  name: string
  role: 'patient'
  user_type: 'patient'
  phone: string
  is_active: boolean
}

const authStore = useAuthStore()
const loading = ref(false)
const patients = ref<PatientUser[]>([])

const search = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const showDeleteDialog = ref(false)
const deleteTarget = ref<PatientUser | null>(null)
const formRef = ref<FormInstance>()

const form = reactive({
  username: '',
  name: '',
  email: '',
  phone: '',
  password: '',
})

const formRules = reactive<FormRules>({
  username: [{ required: true, message: 'Username is required', trigger: 'blur' }],
  name: [{ required: true, message: 'Name is required', trigger: 'blur' }],
})

const canManage = computed(() => authStore.isAdmin)
const canCreatePatient = computed(() => authStore.isAdmin || authStore.isDoctor)

const filteredPatients = computed(() => {
  return patients.value.filter((item) => {
    const text = `${item.username} ${item.name} ${item.email} ${item.phone}`.toLowerCase()
    const hitSearch = !search.value || text.includes(search.value.toLowerCase())
    const hitStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'active' && item.is_active) ||
      (statusFilter.value === 'inactive' && !item.is_active)
    return hitSearch && hitStatus
  })
})

const displayName = (patient: PatientUser) => {
  return patient.name?.trim() || '-'
}

const fetchPatients = async () => {
  const response = await httpClient.get('/api/auth/patients/')
  patients.value = response.data
}

const loadPageData = async () => {
  loading.value = true
  try {
    await fetchPatients()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Failed to load patients')
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.username = ''
  form.name = ''
  form.email = ''
  form.phone = ''
  form.password = ''
}

const openCreate = () => {
  if (!canCreatePatient.value) return
  editingId.value = null
  resetForm()
  showDialog.value = true
}

const openEdit = (patient: PatientUser) => {
  if (!canManage.value) return
  editingId.value = patient.id
  form.username = patient.username
  form.name = patient.name
  form.email = patient.email
  form.phone = patient.phone
  form.password = ''
  showDialog.value = true
}

const closeDialog = () => {
  showDialog.value = false
  formRef.value?.resetFields()
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

const savePatient = async () => {
  if (!formRef.value) return
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  if (editingId.value && !canManage.value) return
  if (!editingId.value && !canCreatePatient.value) return

  const payload = {
    username: form.username.trim(),
    name: form.name.trim(),
    email: form.email.trim(),
    phone: form.phone.trim(),
    ...(form.password.trim() ? { password: form.password.trim() } : {}),
  }

  try {
    if (editingId.value) {
      await httpClient.patch(`/api/auth/patients/${editingId.value}/`, payload)
    } else {
      await httpClient.post('/api/auth/patients/', payload)
    }
    showDialog.value = false
    ElMessage.success(editingId.value ? 'Patient updated' : 'Patient created')
    await fetchPatients()
  } catch (error: any) {
    ElMessage.error(extractErrorMessage(error, 'Save patient failed'))
  }
}

const requestRemovePatient = (patient: PatientUser) => {
  if (!canManage.value) return
  deleteTarget.value = patient
  showDeleteDialog.value = true
}

const closeDeleteDialog = () => {
  showDeleteDialog.value = false
  deleteTarget.value = null
}

const removePatient = async () => {
  if (!canManage.value) return
  if (!deleteTarget.value) return
  try {
    await httpClient.delete(`/api/auth/patients/${deleteTarget.value.id}/`)
    showDeleteDialog.value = false
    deleteTarget.value = null
    ElMessage.success('Patient deleted')
    await fetchPatients()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Delete patient failed')
  }
}

onMounted(async () => {
  await loadPageData()
})
</script>

<template>
  <div class="page">
    <section class="toolbar">
      <div>
        <h2>Patients</h2>
        <p>{{ filteredPatients.length }} patient accounts</p>
      </div>
      <ElButton type="primary" :disabled="!canCreatePatient" @click="openCreate">
        + Add Patient
      </ElButton>
    </section>

    <ElAlert
      v-if="!canManage"
      type="warning"
      :closable="false"
      show-icon
      style="margin-bottom: 16px;"
    >
      Admin can create, edit, and delete patient accounts. Doctors can create patient accounts.
    </ElAlert>

    <section class="filters">
      <ElInput
        v-model="search"
        placeholder="Search patient account"
        clearable
        style="width: 280px;"
      />
      <ElSelect v-model="statusFilter" style="width: 160px;">
        <ElOption label="All status" value="all" />
        <ElOption label="Active" value="active" />
        <ElOption label="Inactive" value="inactive" />
      </ElSelect>
    </section>

    <section class="table-card">
      <ElTable
        v-loading="loading"
        :data="filteredPatients"
        style="width: 100%;"
      >
        <ElTableColumn prop="name" label="Name">
          <template #default="{ row }">
            {{ displayName(row) }}
          </template>
        </ElTableColumn>
        <ElTableColumn prop="email" label="Email">
          <template #default="{ row }">
            {{ row.email || '-' }}
          </template>
        </ElTableColumn>
        <ElTableColumn prop="phone" label="Phone">
          <template #default="{ row }">
            {{ row.phone || '-' }}
          </template>
        </ElTableColumn>
        <ElTableColumn prop="is_active" label="Status" width="120">
          <template #default="{ row }">
            <ElTag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? 'active' : 'inactive' }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="Actions" width="180">
          <template #default="{ row }">
            <ElButton text :disabled="!canManage" @click="openEdit(row)">Edit</ElButton>
            <ElButton text type="danger" :disabled="!canManage" @click="requestRemovePatient(row)">
              Delete
            </ElButton>
          </template>
        </ElTableColumn>
        <template #empty>
          <ElEmpty description="No patients found" />
        </template>
      </ElTable>
    </section>

    <!-- Delete Confirmation Dialog -->
    <ElDialog
      v-model="showDeleteDialog"
      title="Delete Patient Account"
      width="460px"
      :before-close="closeDeleteDialog"
    >
      <p>
        You are about to delete <strong>{{ deleteTarget ? displayName(deleteTarget) : '-' }}</strong>.
        This action cannot be undone.
      </p>
      <template #footer>
        <ElButton @click="closeDeleteDialog">Keep Account</ElButton>
        <ElButton type="danger" @click="removePatient">Delete Permanently</ElButton>
      </template>
    </ElDialog>

    <!-- Create / Edit Dialog -->
    <ElDialog
      v-model="showDialog"
      :title="editingId ? 'Edit Patient' : 'Add Patient'"
      width="560px"
      :before-close="closeDialog"
    >
      <ElForm
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-position="top"
      >
        <ElFormItem label="Username" prop="username">
          <ElInput v-model="form.username" placeholder="Username" />
        </ElFormItem>
        <ElFormItem label="Name" prop="name">
          <ElInput v-model="form.name" placeholder="Name" />
        </ElFormItem>
        <ElFormItem label="Email" prop="email">
          <ElInput v-model="form.email" placeholder="Email" />
        </ElFormItem>
        <ElFormItem label="Phone" prop="phone">
          <ElInput v-model="form.phone" placeholder="Phone" />
        </ElFormItem>
        <ElFormItem label="Password" prop="password">
          <ElInput
            v-model="form.password"
            type="password"
            show-password
            :placeholder="editingId ? 'Reset password (optional)' : 'Initial password (optional)'"
          />
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="closeDialog">Cancel</ElButton>
        <ElButton type="primary" @click="savePatient">Save</ElButton>
      </template>
    </ElDialog>
  </div>
</template>
