<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import httpClient from '@/shared/http'

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

const dateRange = ref<[string, string] | null>(null)
const dateFrom = computed<string>(() => dateRange.value?.[0] || '')
const dateTo = computed<string>(() => dateRange.value?.[1] || '')
const selectedPatientId = ref<number | null>(null)
const selectedDoctorId = ref<number | null>(null)
const page = ref(1)
const pageSize = ref(10)
const totalCount = ref(0)

const displayName = (user: UserOption) => {
  return user.name?.trim() || user.username
}

const hasActiveFilters = computed(
  () => !!dateFrom.value || !!dateTo.value || !!selectedPatientId.value || !!selectedDoctorId.value || pageSize.value !== 10
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

    const response = await httpClient.get('/api/appointments/', {
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
  const response = await httpClient.get('/api/auth/doctors/')
  doctors.value = response.data
}

const fetchPatients = async () => {
  const response = await httpClient.get('/api/auth/patients/')
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
        unlink-panels
        range-separator="—"
        start-placeholder="Start date"
        end-placeholder="End date"
        value-format="YYYY-MM-DD"
        class="filter-control filter-date-range"
      />
      <el-select
        v-model="selectedPatientId"
        placeholder="All patients"
        clearable
        class="filter-control"
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
        class="filter-control"
      >
        <el-option
          v-for="doctor in doctors"
          :key="doctor.id"
          :label="displayName(doctor)"
          :value="doctor.id"
        />
      </el-select>
      <div class="filter-actions">
        <el-button type="primary" class="filter-apply" @click="applyFilters">Apply</el-button>
        <el-button class="filter-reset" :disabled="!hasActiveFilters" @click="resetFilters">Reset</el-button>
      </div>
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
        class="cards-grid-empty"
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
      class="record-detail-dialog"
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

.records-filters {
  display: grid !important;
  grid-template-columns: minmax(320px, 360px) minmax(150px, 1fr) minmax(150px, 1fr) auto;
  gap: 12px;
  align-items: center;
}

.filter-date-range :deep(.el-range-editor.el-input__wrapper) {
  width: 100% !important;
}

.cards-grid-empty {
  grid-column: 1 / -1;
  width: 100%;
  padding: 32px 16px;
}

.filter-control {
  width: 100% !important;
  min-width: 0;
}

.filter-control :deep(.el-input__wrapper),
.filter-control :deep(.el-range-editor.el-input__wrapper) {
  background-color: #f8fbff;
  border-radius: 12px;
  box-shadow: 0 0 0 1px #cfd9ec inset;
  padding: 0 12px;
  min-height: 42px;
  transition: box-shadow 0.18s ease, background-color 0.18s ease;
}

.filter-control :deep(.el-input__wrapper:hover),
.filter-control :deep(.el-range-editor.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #b8c7e3 inset;
}

.filter-control :deep(.el-input.is-focus .el-input__wrapper),
.filter-control :deep(.el-range-editor.is-active.el-input__wrapper) {
  background-color: #ffffff;
  box-shadow: 0 0 0 1px #3f67ea inset, 0 0 0 3px rgba(63, 103, 234, 0.14);
}

.filter-control :deep(.el-input__inner),
.filter-control :deep(.el-range-input) {
  border: 0 !important;
  background: transparent !important;
  height: 40px !important;
  font-size: 13px !important;
  color: #1f2f4e !important;
  box-shadow: none !important;
}

.filter-control :deep(.el-input__inner::placeholder),
.filter-control :deep(.el-range-input::placeholder) {
  color: #95a3c2;
}

.filter-control :deep(.el-range-separator) {
  color: #95a3c2;
  font-size: 12px;
  line-height: 40px;
  padding: 0 4px;
}

.filter-control :deep(.el-input__prefix-inner),
.filter-control :deep(.el-input__suffix-inner) {
  color: #8895b6;
}

.filter-actions {
  display: inline-flex;
  gap: 8px;
  white-space: nowrap;
}

.filter-actions :deep(.el-button) {
  height: 42px;
  border-radius: 12px;
  padding: 0 18px;
  font-weight: 600;
  font-size: 13px;
  margin: 0;
}

.filter-apply :deep(.el-button),
.filter-actions :deep(.el-button.filter-apply),
.filter-actions :deep(.filter-apply) {
  border: 0;
  background: linear-gradient(135deg, #3e66e9 0%, #3058d9 100%);
  box-shadow: 0 6px 14px rgba(48, 88, 217, 0.18);
  color: #ffffff;
}

.filter-actions :deep(.filter-apply:hover) {
  filter: brightness(1.04);
  box-shadow: 0 10px 22px rgba(48, 88, 217, 0.26);
  transform: translateY(-1px);
}

.filter-actions :deep(.filter-reset) {
  border: 1px solid #cfd9ec;
  background: #f8fbff;
  color: #4a587c;
}

.filter-actions :deep(.filter-reset:hover:not(:disabled)) {
  border-color: #b8c7e3;
  background: #eef3fb;
}

.filter-actions :deep(.filter-reset:disabled) {
  opacity: 0.55;
  cursor: not-allowed;
}

@media (max-width: 1180px) {
  .records-filters {
    grid-template-columns: 1fr 1fr;
  }
  .filter-date-range {
    grid-column: 1 / -1;
  }
  .filter-actions {
    grid-column: 1 / -1;
    justify-content: flex-end;
  }
}
</style>

<style>
.record-detail-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 24px 60px rgba(20, 38, 80, 0.22);
}

.record-detail-dialog .el-dialog__header {
  margin: 0;
  padding: 18px 22px 14px;
  border-bottom: 1px solid #eef2f7;
}

.record-detail-dialog .el-dialog__title {
  font-size: 17px;
  font-weight: 700;
  color: #1b2a4a;
  letter-spacing: -0.1px;
}

.record-detail-dialog .el-dialog__headerbtn {
  top: 14px;
  right: 14px;
}

.record-detail-dialog .el-dialog__close {
  color: #8895b6;
  font-size: 18px;
}

.record-detail-dialog .el-dialog__close:hover {
  color: #3058d9;
}

.record-detail-dialog .el-dialog__body {
  padding: 18px 22px;
}

.record-detail-dialog .el-dialog__footer {
  padding: 14px 22px 18px;
  border-top: 1px solid #eef2f7;
}

.record-detail-dialog .el-descriptions {
  width: 100%;
}

.record-detail-dialog .el-descriptions__body {
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid #e6ecf6;
  background: #ffffff;
}

.record-detail-dialog .el-descriptions__body .el-descriptions__table {
  width: 100% !important;
  table-layout: fixed !important;
}

.record-detail-dialog .el-descriptions__cell {
  border-color: #eaf0f8 !important;
  word-break: break-word;
  vertical-align: top;
}

.record-detail-dialog .el-descriptions__label {
  background: #f8fbff !important;
  color: #475982 !important;
  font-size: 12.5px !important;
  font-weight: 600 !important;
  letter-spacing: 0.1px;
  padding: 12px 14px !important;
  width: 130px;
}

.record-detail-dialog .el-descriptions__content {
  font-size: 13px !important;
  color: #1f2f4e !important;
  padding: 12px 14px !important;
  background: #ffffff !important;
  line-height: 1.55;
}

.record-detail-dialog .el-dialog__footer .el-button {
  height: 38px;
  border-radius: 10px;
  padding: 0 18px;
  font-weight: 600;
  font-size: 13px;
  border: 1px solid #cfd9ec;
  background: #f8fbff;
  color: #4a587c;
}

.record-detail-dialog .el-dialog__footer .el-button:hover {
  border-color: #b8c7e3;
  background: #eef3fb;
}
</style>
