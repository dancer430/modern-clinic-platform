<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
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
  name: string
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

const loading = ref(false)
const selectedRecord = ref<RecordViewItem | null>(null)
const records = ref<RecordViewItem[]>([])
const doctors = ref<UserOption[]>([])
const patients = ref<UserOption[]>([])

const dateRange = ref<[Date, Date] | null>(null)
const selectedPatientId = ref<number | null>(null)
const selectedDoctorId = ref<number | null>(null)
const page = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)

const displayName = (user: UserOption) => {
  return user.name?.trim() || user.username
}

const dateFrom = computed(() => {
  if (!dateRange.value) return ''
  const d = dateRange.value[0]
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

const dateTo = computed(() => {
  if (!dateRange.value) return ''
  const d = dateRange.value[1]
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
})

const hasActiveFilters = computed(
  () => !!dateRange.value || !!selectedPatientId.value || !!selectedDoctorId.value || pageSize.value !== 10
)

const recordsSorted = computed(() => {
  return records.value
})

const showDetailDialog = computed({
  get: () => selectedRecord.value !== null,
  set: (val: boolean) => { if (!val) selectedRecord.value = null },
})

const fetchCompletedRecords = async () => {
  loading.value = true
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
    ElMessage.error(error.response?.data?.detail || 'Failed to load medical records')
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
  page.value = 1
  await fetchCompletedRecords()
}

const resetFilters = async () => {
  dateRange.value = null
  selectedDoctorId.value = null
  selectedPatientId.value = null
  page.value = 1
  pageSize.value = 10
  await fetchCompletedRecords()
}

const handlePageChange = async (newPage: number) => {
  page.value = newPage
  await fetchCompletedRecords()
}

const handleSizeChange = async (newSize: number) => {
  pageSize.value = newSize
  page.value = 1
  await fetchCompletedRecords()
}

const openDetail = (record: RecordViewItem) => {
  selectedRecord.value = record
}

onMounted(async () => {
  try {
    await Promise.all([fetchDoctors(), fetchPatients()])
  } catch {
    // non-blocking for records listing
  }
  await fetchCompletedRecords()
})
</script>

<template>
  <div class="page" v-loading="loading">
    <section class="toolbar">
      <div>
        <h2>Medical Records</h2>
        <p>Showing completed appointments as record thumbnails. Click to view details.</p>
      </div>
    </section>

    <section class="filters records-filters">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="to"
        start-placeholder="Start date"
        end-placeholder="End date"
        clearable
        style="width: 280px"
      />
      <el-select
        v-model="selectedPatientId"
        placeholder="All patients"
        clearable
        style="width: 180px"
      >
        <el-option
          v-for="patient in patients"
          :key="patient.id"
          :label="displayName(patient)"
          :value="patient.id"
        />
      </el-select>
      <el-select
        v-model="selectedDoctorId"
        placeholder="All doctors"
        clearable
        style="width: 180px"
      >
        <el-option
          v-for="doctor in doctors"
          :key="doctor.id"
          :label="displayName(doctor)"
          :value="doctor.id"
        />
      </el-select>
      <el-button @click="applyFilters">Apply</el-button>
      <el-button :disabled="!hasActiveFilters" @click="resetFilters">Reset</el-button>
    </section>

    <section class="cards-grid">
      <el-card
        v-for="item in recordsSorted"
        :key="item.id"
        class="record-card record-thumbnail"
        shadow="hover"
        role="button"
        tabindex="0"
        @click="openDetail(item)"
        @keydown.enter="openDetail(item)"
      >
        <template #header>
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <h3 style="margin: 0;">{{ item.patient_name }}</h3>
            <el-tag type="success" size="small">completed</el-tag>
          </div>
        </template>
        <p><strong>Doctor:</strong> {{ item.doctor_name }}</p>
        <p><strong>Visit:</strong> {{ item.appointment_date }} &middot; {{ item.appointment_time.slice(0, 5) }}</p>
        <p class="record-clip"><strong>Diagnosis:</strong> {{ item.diagnosis_result || '-' }}</p>
      </el-card>

      <el-empty
        v-if="!loading && recordsSorted.length === 0"
        description="No completed records available for current user scope."
      />
    </section>

    <section class="table-card pagination-bar">
      <el-pagination
        :current-page="page"
        :page-size="pageSize"
        :total="totalCount"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </section>

    <el-dialog
      v-model="showDetailDialog"
      title="Medical Record Detail"
      width="680px"
      destroy-on-close
    >
      <el-descriptions v-if="selectedRecord" :column="2" border>
        <el-descriptions-item label="Patient">{{ selectedRecord.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="Doctor">{{ selectedRecord.doctor_name }}</el-descriptions-item>
        <el-descriptions-item label="Visit Date">{{ selectedRecord.appointment_date }}</el-descriptions-item>
        <el-descriptions-item label="Visit Time">{{ selectedRecord.appointment_time.slice(0, 5) }}</el-descriptions-item>
        <el-descriptions-item label="Chief Reason" :span="2">{{ selectedRecord.reason || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Confirm Info" :span="2">{{ selectedRecord.confirm_info || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Diagnosis Result" :span="2">{{ selectedRecord.diagnosis_result || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Treatment Plan" :span="2">{{ selectedRecord.treatment_plan || '-' }}</el-descriptions-item>
        <el-descriptions-item label="Medical Advice" :span="2">{{ selectedRecord.medical_advice || '-' }}</el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="showDetailDialog = false">Close</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.record-card.record-thumbnail {
  cursor: pointer;
}
</style>
