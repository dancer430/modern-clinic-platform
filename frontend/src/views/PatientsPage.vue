<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import apiClient from '@/utils/apiClient'
import { useAuthStore } from '@/stores/auth'

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
const errorMessage = ref('')
const patients = ref<PatientUser[]>([])

const search = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const showDeleteDialog = ref(false)
const deleteTarget = ref<PatientUser | null>(null)
const submitAttempted = ref(false)

const form = ref({
  username: '',
  name: '',
  email: '',
  phone: '',
  password: '',
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
  const response = await apiClient.get('/api/auth/patients/')
  patients.value = response.data
}

const loadPageData = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    await fetchPatients()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to load patients'
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
  if (!canCreatePatient.value) return
  editingId.value = null
  resetForm()
  submitAttempted.value = false
  showDialog.value = true
}

const openEdit = (patient: PatientUser) => {
  if (!canManage.value) return
  editingId.value = patient.id
  form.value = {
    username: patient.username,
    name: patient.name,
    email: patient.email,
    phone: patient.phone,
    password: '',
  }
  submitAttempted.value = false
  showDialog.value = true
}

const formInvalid = computed(
  () => !form.value.username.trim() || !form.value.name.trim()
)

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
  submitAttempted.value = true
  if (formInvalid.value) return
  if (editingId.value && !canManage.value) return
  if (!editingId.value && !canCreatePatient.value) return

  const payload = {
    username: form.value.username.trim(),
    name: form.value.name.trim(),
    email: form.value.email.trim(),
    phone: form.value.phone.trim(),
    ...(form.value.password.trim() ? { password: form.value.password.trim() } : {}),
  }

  try {
    if (editingId.value) {
      await apiClient.patch(`/api/auth/patients/${editingId.value}/`, payload)
    } else {
      await apiClient.post('/api/auth/patients/', payload)
    }
    showDialog.value = false
    await fetchPatients()
  } catch (error: any) {
    errorMessage.value = extractErrorMessage(error, 'Save patient failed')
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
    await apiClient.delete(`/api/auth/patients/${deleteTarget.value.id}/`)
    showDeleteDialog.value = false
    deleteTarget.value = null
    await fetchPatients()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Delete patient failed'
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
      <button class="primary" :disabled="!canCreatePatient" @click="openCreate">+ Add Patient</button>
    </section>

    <section v-if="errorMessage" class="table-card" style="padding: 10px 12px; color: #c2334a;">
      {{ errorMessage }}
    </section>

    <section v-if="!canManage" class="table-card" style="padding: 10px 12px; color: #9b6d00;">
      Admin can create, edit, and delete patient accounts. Doctors can create patient accounts.
    </section>

    <section class="filters">
      <input v-model="search" placeholder="Search patient account" />
      <select v-model="statusFilter">
        <option value="all">All status</option>
        <option value="active">active</option>
        <option value="inactive">inactive</option>
      </select>
    </section>

    <section class="table-card">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="patient in filteredPatients" :key="patient.id">
            <td>{{ displayName(patient) }}</td>
            <td>{{ patient.email || '-' }}</td>
            <td>{{ patient.phone || '-' }}</td>
            <td><span class="badge" :class="patient.is_active ? 'confirmed' : 'cancelled'">{{ patient.is_active ? 'active' : 'inactive' }}</span></td>
            <td class="actions-cell">
              <button class="ghost action-btn" :disabled="!canManage" @click="openEdit(patient)">Edit</button>
              <button class="danger action-btn" :disabled="!canManage" @click="requestRemovePatient(patient)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <div v-if="showDeleteDialog" class="overlay" @click.self="closeDeleteDialog">
      <div class="dialog" style="max-width: 460px;">
        <h3>Delete Patient Account</h3>
        <p class="dialog-tip danger-text">
          You are about to delete <strong>{{ deleteTarget ? displayName(deleteTarget) : '-' }}</strong>. This action cannot be undone.
        </p>
        <div class="actions">
          <button class="ghost" @click="closeDeleteDialog">Keep Account</button>
          <button class="danger" @click="removePatient">Delete Permanently</button>
        </div>
      </div>
    </div>

    <div v-if="showDialog" class="overlay" @click.self="showDialog = false; submitAttempted = false">
      <div class="dialog">
        <h3>{{ editingId ? 'Edit Patient' : 'Add Patient' }}</h3>
        <div class="grid">
          <input v-model="form.username" placeholder="Username *" :class="{ 'input-invalid': submitAttempted && !form.username.trim() }" />
          <input v-model="form.name" placeholder="Name *" :class="{ 'input-invalid': submitAttempted && !form.name.trim() }" />
          <input v-model="form.email" placeholder="Email" />
          <input v-model="form.phone" placeholder="Phone" />
          <input v-model="form.password" type="password" :placeholder="editingId ? 'Reset password (optional)' : 'Initial password (optional)'" />
        </div>
        <div class="actions">
          <button class="ghost" @click="showDialog = false; submitAttempted = false">Cancel</button>
          <button class="primary" @click="savePatient">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
