<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import apiClient from '@/utils/apiClient'

interface RecordViewItem {
  id: number
  patient: number
  patient_name: string
  doctor: number
  doctor_name: string
  appointment_date: string
  appointment_time: string
  reason: string
  confirm_info: string
  diagnosis_result: string
  treatment_plan: string
  medical_advice: string
}

interface UserOption {
  id: number
  username: string
  first_name: string
  last_name: string
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

const loading = ref(false)
const errorMessage = ref('')
const filterMessage = ref('')
const selectedRecord = ref<RecordViewItem | null>(null)
const records = ref<RecordViewItem[]>([])
const doctors = ref<UserOption[]>([])
const patients = ref<UserOption[]>([])

const dateFrom = ref('')
const dateTo = ref('')
const draftDateFrom = ref('')
const draftDateTo = ref('')
const showRangePicker = ref(false)
const selectedPatientId = ref<number | null>(null)
const selectedDoctorId = ref<number | null>(null)
const page = ref(1)
const pageSize = ref<10 | 20 | 50>(10)
const totalCount = ref(0)

const displayName = (user: UserOption) => {
  const fullName = `${user.first_name} ${user.last_name}`.trim()
  return fullName || user.username
}

const hasActiveFilters = computed(
  () => !!dateFrom.value || !!dateTo.value || !!selectedPatientId.value || !!selectedDoctorId.value || pageSize.value !== 10
)

const recordsSorted = computed(() => {
  return records.value
})

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))
const pageStart = computed(() => (totalCount.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1))
const pageEnd = computed(() => Math.min(totalCount.value, page.value * pageSize.value))

const fetchCompletedRecords = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const params: Record<string, string> = {
      status: 'completed',
      page: String(page.value),
      page_size: String(pageSize.value),
    }

    if (selectedDoctorId.value) {
      params.doctor = String(selectedDoctorId.value)
    }
    if (selectedPatientId.value) {
      params.patient = String(selectedPatientId.value)
    }
    if (dateFrom.value) {
      params.date_from = dateFrom.value
    }
    if (dateTo.value) {
      params.date_to = dateTo.value
    }

    const response = await apiClient.get('/api/appointments/', {
      params,
    })
    const data = response.data as PaginatedResponse<RecordViewItem> | RecordViewItem[]
    if (Array.isArray(data)) {
      records.value = data
      totalCount.value = data.length
      return
    }
    records.value = data.results
    totalCount.value = data.count
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to load medical records'
  } finally {
    loading.value = false
  }
}

const fetchDoctors = async () => {
  const response = await apiClient.get('/api/auth/doctors/')
  doctors.value = response.data
}

const fetchPatients = async () => {
  const response = await apiClient.get('/api/auth/patients/')
  patients.value = response.data
}

const applyFilters = async () => {
  if ((dateFrom.value && !dateTo.value) || (!dateFrom.value && dateTo.value)) {
    filterMessage.value = 'Please select both start and end date for range filtering.'
    return
  }
  filterMessage.value = ''
  page.value = 1
  await fetchCompletedRecords()
}

const resetFilters = async () => {
  filterMessage.value = ''
  dateFrom.value = ''
  dateTo.value = ''
  draftDateFrom.value = ''
  draftDateTo.value = ''
  showRangePicker.value = false
  selectedDoctorId.value = null
  selectedPatientId.value = null
  page.value = 1
  pageSize.value = 10
  await fetchCompletedRecords()
}

const goPrevPage = async () => {
  if (page.value <= 1) return
  page.value -= 1
  await fetchCompletedRecords()
}

const goNextPage = async () => {
  if (page.value >= totalPages.value) return
  page.value += 1
  await fetchCompletedRecords()
}

const fillDateToToday = () => {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  const today = `${year}-${month}-${day}`
  dateTo.value = today
  draftDateTo.value = today
}

const dateRangeLabel = computed(() => {
  if (dateFrom.value && dateTo.value) {
    return `${dateFrom.value.slice(5)} - ${dateTo.value.slice(5)}`
  }
  return 'Date range'
})

const openRangePicker = () => {
  draftDateFrom.value = dateFrom.value
  draftDateTo.value = dateTo.value
  showRangePicker.value = true
}

const closeRangePicker = () => {
  showRangePicker.value = false
}

const clearRangePicker = () => {
  draftDateFrom.value = ''
  draftDateTo.value = ''
}

const applyRangePicker = () => {
  if (!draftDateFrom.value || !draftDateTo.value) {
    filterMessage.value = 'Please select both start and end date for range filtering.'
    return
  }
  filterMessage.value = ''
  dateFrom.value = draftDateFrom.value
  dateTo.value = draftDateTo.value
  showRangePicker.value = false
}

const openDetail = (record: RecordViewItem) => {
  selectedRecord.value = record
}

const closeDetail = () => {
  selectedRecord.value = null
}

onMounted(async () => {
  try {
    await Promise.all([fetchDoctors(), fetchPatients()])
  } catch {
    // non-blocking for records listing
  }
  await fetchCompletedRecords()
})

watch(pageSize, async () => {
  page.value = 1
  await fetchCompletedRecords()
})
</script>

<template>
  <div class="page">
    <section class="toolbar">
      <div>
        <h2>Medical Records</h2>
        <p>Showing completed appointments as record thumbnails. Click to view details.</p>
      </div>
    </section>

    <section v-if="errorMessage" class="table-card" style="padding: 10px 12px; color: #c2334a;">
      {{ errorMessage }}
    </section>
    <section v-if="filterMessage" class="table-card" style="padding: 10px 12px; color: #c2334a;">
      {{ filterMessage }}
    </section>

    <section class="filters records-filters">
      <div class="date-range-picker">
        <button class="range-trigger" type="button" @click="openRangePicker">
          <span class="range-trigger-text">{{ dateRangeLabel }}</span>
        </button>
        <div v-if="showRangePicker" class="range-popover">
          <label>Start date</label>
          <input v-model="draftDateFrom" type="date" />
          <label>End date</label>
          <input v-model="draftDateTo" type="date" />
          <div class="range-popover-actions">
            <button class="ghost tiny-btn" type="button" @click="fillDateToToday">End: today</button>
            <button class="ghost tiny-btn" type="button" @click="clearRangePicker">Clear</button>
            <button class="ghost tiny-btn" type="button" @click="closeRangePicker">Cancel</button>
            <button class="primary tiny-btn" type="button" @click="applyRangePicker">Apply range</button>
          </div>
        </div>
      </div>
      <select v-model.number="selectedPatientId">
        <option :value="null">All patients</option>
        <option v-for="patient in patients" :key="patient.id" :value="patient.id">{{ displayName(patient) }}</option>
      </select>
      <select v-model.number="selectedDoctorId">
        <option :value="null">All doctors</option>
        <option v-for="doctor in doctors" :key="doctor.id" :value="doctor.id">{{ displayName(doctor) }}</option>
      </select>
      <div class="tabs">
        <button class="ghost" @click="applyFilters">Apply</button>
        <button class="ghost" :disabled="!hasActiveFilters" @click="resetFilters">Reset</button>
      </div>
    </section>

    <section class="cards-grid">
      <article
        v-for="item in recordsSorted"
        :key="item.id"
        class="record-card record-thumbnail"
        role="button"
        tabindex="0"
        @click="openDetail(item)"
        @keydown.enter="openDetail(item)"
      >
        <header>
          <h3>{{ item.patient_name }}</h3>
          <span class="badge completed">completed</span>
        </header>
        <p><strong>Doctor:</strong> {{ item.doctor_name }}</p>
        <p><strong>Visit:</strong> {{ item.appointment_date }} · {{ item.appointment_time.slice(0, 5) }}</p>
        <p class="record-clip"><strong>Diagnosis:</strong> {{ item.diagnosis_result || '-' }}</p>
      </article>

      <article v-if="!loading && recordsSorted.length === 0" class="record-card record-empty">
        <p>No completed records available for current user scope.</p>
      </article>
    </section>

    <section class="table-card pagination-bar">
      <div class="pagination-summary">
        <strong>{{ pageStart }}-{{ pageEnd }}</strong>
        <span>of {{ totalCount }} records</span>
      </div>
      <div class="pagination-controls">
        <label class="page-size-wrap">
          <span>Rows</span>
          <select v-model.number="pageSize" class="page-size-select">
          <option :value="10">10 / page</option>
          <option :value="20">20 / page</option>
          <option :value="50">50 / page</option>
          </select>
        </label>
        <div class="tabs pagination-nav">
          <button class="ghost pager-btn" :disabled="page <= 1" @click="goPrevPage">‹</button>
          <span class="page-index">Page {{ page }} / {{ totalPages }}</span>
          <button class="ghost pager-btn" :disabled="page >= totalPages" @click="goNextPage">›</button>
        </div>
      </div>
    </section>

    <div v-if="selectedRecord" class="overlay" @click.self="closeDetail">
      <div class="dialog record-detail-dialog">
        <h3>Medical Record Detail</h3>
        <div class="record-detail-grid">
          <p><strong>Patient:</strong> {{ selectedRecord.patient_name }}</p>
          <p><strong>Doctor:</strong> {{ selectedRecord.doctor_name }}</p>
          <p><strong>Visit Date:</strong> {{ selectedRecord.appointment_date }}</p>
          <p><strong>Visit Time:</strong> {{ selectedRecord.appointment_time.slice(0, 5) }}</p>
          <p class="full-width"><strong>Chief Reason:</strong> {{ selectedRecord.reason || '-' }}</p>
          <p class="full-width"><strong>Confirm Info:</strong> {{ selectedRecord.confirm_info || '-' }}</p>
          <p class="full-width"><strong>Diagnosis Result:</strong> {{ selectedRecord.diagnosis_result || '-' }}</p>
          <p class="full-width"><strong>Treatment Plan:</strong> {{ selectedRecord.treatment_plan || '-' }}</p>
          <p class="full-width"><strong>Medical Advice:</strong> {{ selectedRecord.medical_advice || '-' }}</p>
        </div>
        <div class="actions">
          <button class="ghost" @click="closeDetail">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>
