<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import apiClient from '@/utils/apiClient'
import { useAuthStore } from '@/stores/auth'

interface DoctorUser {
  id: number
  username: string
  email: string
  first_name: string
  last_name: string
  role: 'doctor'
  user_type: 'doctor'
  phone: string
  is_active: boolean
}

const authStore = useAuthStore()
const loading = ref(false)
const errorMessage = ref('')
const doctors = ref<DoctorUser[]>([])

const query = ref('')
const statusFilter = ref<'all' | 'active' | 'inactive'>('all')
const showDialog = ref(false)
const editingId = ref<number | null>(null)
const showDeleteDialog = ref(false)
const deleteTarget = ref<DoctorUser | null>(null)
const submitAttempted = ref(false)

const form = ref({
  username: '',
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  password: '',
})

const canManage = computed(() => authStore.isAdmin)

const filteredDoctors = computed(() => {
  return doctors.value.filter((item) => {
    const text = `${item.username} ${item.first_name} ${item.last_name} ${item.email} ${item.phone}`.toLowerCase()
    const hitSearch = !query.value || text.includes(query.value.toLowerCase())
    const hitStatus =
      statusFilter.value === 'all' ||
      (statusFilter.value === 'active' && item.is_active) ||
      (statusFilter.value === 'inactive' && !item.is_active)
    return hitSearch && hitStatus
  })
})

const displayName = (doctor: DoctorUser) => {
  const fullName = `${doctor.first_name} ${doctor.last_name}`.trim()
  return fullName || doctor.username
}

const fetchDoctors = async () => {
  const response = await apiClient.get('/api/auth/doctors/')
  doctors.value = response.data
}

const loadPageData = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    await fetchDoctors()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to load doctors'
  } finally {
    loading.value = false
  }
}

const resetForm = () => {
  form.value = {
    username: '',
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    password: '',
  }
}

const openCreate = () => {
  if (!canManage.value) return
  editingId.value = null
  resetForm()
  submitAttempted.value = false
  showDialog.value = true
}

const openEdit = (doctor: DoctorUser) => {
  if (!canManage.value) return
  editingId.value = doctor.id
  form.value = {
    username: doctor.username,
    first_name: doctor.first_name,
    last_name: doctor.last_name,
    email: doctor.email,
    phone: doctor.phone,
    password: '',
  }
  submitAttempted.value = false
  showDialog.value = true
}

const formInvalid = computed(
  () =>
    !form.value.username.trim() ||
    !form.value.first_name.trim() ||
    !form.value.last_name.trim() ||
    !form.value.email.trim() ||
    !form.value.phone.trim()
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

const saveDoctor = async () => {
  submitAttempted.value = true
  if (!canManage.value || formInvalid.value) return

  const payload = {
    username: form.value.username.trim(),
    first_name: form.value.first_name.trim(),
    last_name: form.value.last_name.trim(),
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
    await fetchDoctors()
  } catch (error: any) {
    errorMessage.value = extractErrorMessage(error, 'Save doctor failed')
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
    await fetchDoctors()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Delete doctor failed'
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
        <h2>Doctors</h2>
        <p>{{ filteredDoctors.length }} doctor accounts</p>
      </div>
      <button class="primary" :disabled="!canManage" @click="openCreate">+ Add Doctor</button>
    </section>

    <section v-if="errorMessage" class="table-card" style="padding: 10px 12px; color: #c2334a;">
      {{ errorMessage }}
    </section>

    <section v-if="!canManage" class="table-card" style="padding: 10px 12px; color: #9b6d00;">
      Only admin can create, edit, or delete doctor accounts.
    </section>

    <section class="filters">
      <input v-model="query" placeholder="Search doctor account" />
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
            <th>Username</th>
            <th>Email</th>
            <th>Phone</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doctor in filteredDoctors" :key="doctor.id">
            <td>{{ displayName(doctor) }}</td>
            <td>{{ doctor.username }}</td>
            <td>{{ doctor.email || '-' }}</td>
            <td>{{ doctor.phone || '-' }}</td>
            <td><span class="badge" :class="doctor.is_active ? 'confirmed' : 'cancelled'">{{ doctor.is_active ? 'active' : 'inactive' }}</span></td>
            <td class="actions-cell">
              <button class="ghost action-btn" :disabled="!canManage" @click="openEdit(doctor)">Edit</button>
              <button class="danger action-btn" :disabled="!canManage" @click="requestRemoveDoctor(doctor)">Delete</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <div v-if="showDeleteDialog" class="overlay" @click.self="closeDeleteDialog">
      <div class="dialog" style="max-width: 460px;">
        <h3>Delete Doctor Account</h3>
        <p class="dialog-tip danger-text">
          You are about to delete <strong>{{ deleteTarget ? displayName(deleteTarget) : '-' }}</strong>. This action cannot be undone.
        </p>
        <div class="actions">
          <button class="ghost" @click="closeDeleteDialog">Keep Account</button>
          <button class="danger" @click="removeDoctor">Delete Permanently</button>
        </div>
      </div>
    </div>

    <div v-if="showDialog" class="overlay" @click.self="showDialog = false; submitAttempted = false">
      <div class="dialog">
        <h3>{{ editingId ? 'Edit Doctor' : 'Add Doctor' }}</h3>
        <div class="grid">
          <input v-model="form.username" placeholder="Username *" :class="{ 'input-invalid': submitAttempted && !form.username.trim() }" />
          <input v-model="form.first_name" placeholder="First name *" :class="{ 'input-invalid': submitAttempted && !form.first_name.trim() }" />
          <input v-model="form.last_name" placeholder="Last name *" :class="{ 'input-invalid': submitAttempted && !form.last_name.trim() }" />
          <input v-model="form.email" placeholder="Email *" :class="{ 'input-invalid': submitAttempted && !form.email.trim() }" />
          <input v-model="form.phone" placeholder="Phone *" :class="{ 'input-invalid': submitAttempted && !form.phone.trim() }" />
          <input v-model="form.password" type="password" :placeholder="editingId ? 'Reset password (optional)' : 'Initial password (optional)'" />
        </div>
        <div class="actions">
          <button class="ghost" @click="showDialog = false; submitAttempted = false">Cancel</button>
          <button class="primary" @click="saveDoctor">Save</button>
        </div>
      </div>
    </div>
  </div>
</template>
