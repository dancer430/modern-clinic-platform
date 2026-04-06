<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import apiClient from '@/utils/apiClient'
import { useAuthStore } from '@/stores/auth'
import { compressImage, validateImageFile } from '@/utils/imageUtils'

type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled'

interface AppointmentItem {
  id: number
  patient: number
  patient_name: string
  doctor: number
  doctor_name: string
  appointment_date: string
  appointment_time: string
  reason: string
  status: AppointmentStatus
  confirm_info: string
  diagnosis_result: string
  treatment_plan: string
  medical_advice: string
  attachments?: Array<{
    id: number
    file_name: string
    image_data: string
    image_type: string
    compressed_size: number
    created_at: string
  }>
}

interface CompleteAttachmentItem {
  file_name: string
  image_data: string
  image_type: string
  compressed_size: number
}

interface UserOption {
  id: number
  username: string
  name: string
  user_type: 'admin' | 'doctor' | 'patient'
}

interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

const SLOT_TIMES = [
  '08:00',
  '08:30',
  '09:00',
  '09:30',
  '10:00',
  '10:30',
  '11:00',
  '11:30',
  '14:00',
  '14:30',
  '15:00',
  '15:30',
  '16:00',
  '16:30',
  '17:00',
]

const toLocalDateString = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const loading = ref(false)

const appointments = ref<AppointmentItem[]>([])
const doctors = ref<UserOption[]>([])
const patients = ref<UserOption[]>([])
const scheduleSlots = ref<Array<{ doctor: number; slot_date: string; slot_time: string; is_available: boolean }>>([])

const search = ref('')
const status = ref<'all' | AppointmentStatus>('all')
const page = ref(1)
const pageSize = ref<10 | 20 | 50>(10)
const totalCount = ref(0)
const showDialog = ref(false)
const showConfirmDialog = ref(false)
const showCompleteDialog = ref(false)
const showCancelDialog = ref(false)
const createSubmitAttempted = ref(false)

const confirmTargetId = ref<number | null>(null)
const confirmInfoForm = ref('')

const completeTargetId = ref<number | null>(null)
const cancelTargetId = ref<number | null>(null)
const completeAttachmentInputRef = ref<HTMLInputElement | null>(null)
const completeUploaderDragging = ref(false)
const completeSubmitAttempted = ref(false)
const completeForm = ref({
  diagnosisResult: '',
  treatmentPlan: '',
  medicalAdvice: '',
  createNextAppointment: false,
  attachments: [] as CompleteAttachmentItem[],
})

const form = ref({
  patient: null as number | null,
  doctor: null as number | null,
  date: toLocalDateString(new Date()),
  time: '',
  reason: '',
})

const displayName = (user: UserOption) => user.name?.trim() || user.username

const filtered = computed(() => {
  return appointments.value
})

const totalPages = computed(() => Math.max(1, Math.ceil(totalCount.value / pageSize.value)))
const pageStart = computed(() => (totalCount.value === 0 ? 0 : (page.value - 1) * pageSize.value + 1))
const pageEnd = computed(() => Math.min(totalCount.value, page.value * pageSize.value))

const cancelTarget = computed(
  () => appointments.value.find((item) => item.id === cancelTargetId.value) || null
)

const cancelDialogMessage = computed(() => {
  if (!cancelTarget.value) return 'Cancel this appointment?'
  return `Cancel appointment for ${cancelTarget.value.patient_name} on ${cancelTarget.value.appointment_date} ${cancelTarget.value.appointment_time.slice(0, 5)}?`
})

const bookedCount = (doctorId: number, date: string, time: string) => {
  return appointments.value.filter(
    (item) =>
      item.doctor === doctorId &&
      item.appointment_date === date &&
      item.appointment_time.slice(0, 5) === time &&
      item.status !== 'cancelled'
  ).length
}

const isBlocked = (doctorId: number, date: string, time: string) => {
  return scheduleSlots.value.some(
    (slot) =>
      slot.doctor === doctorId &&
      slot.slot_date === date &&
      slot.slot_time.slice(0, 5) === time &&
      slot.is_available === false
  )
}

const slotOptions = computed(() => {
  if (!form.value.doctor || !form.value.date) return []
  return SLOT_TIMES.map((time) => {
    const blocked = isBlocked(form.value.doctor as number, form.value.date, time)
    const booked = bookedCount(form.value.doctor as number, form.value.date, time)
    return {
      time,
      blocked,
      booked,
      label: blocked ? `${time} \u00b7 unavailable` : `${time} \u00b7 ${booked} booked`,
    }
  })
})

const confirmInfoTooLong = computed(() => confirmInfoForm.value.length > 500)
const completeFormInvalid = computed(
  () => !completeForm.value.diagnosisResult.trim() || !completeForm.value.treatmentPlan.trim()
)
const showSqliteAttachmentHint = computed(() => authStore.user?.db_vendor === 'sqlite')

const canConfirm = (item: AppointmentItem) =>
  item.status === 'pending' && (authStore.isAdmin || (authStore.isDoctor && item.doctor === authStore.user?.id))

const canComplete = (item: AppointmentItem) =>
  item.status === 'confirmed' && (authStore.isAdmin || (authStore.isDoctor && item.doctor === authStore.user?.id))

const statusTagType = (s: AppointmentStatus) => {
  switch (s) {
    case 'pending': return 'warning'
    case 'confirmed': return ''
    case 'completed': return 'success'
    case 'cancelled': return 'danger'
    default: return 'info'
  }
}

const fetchAppointments = async () => {
  const params: Record<string, string | number> = {
    page: page.value,
    page_size: pageSize.value,
  }
  if (status.value !== 'all') {
    params.status = status.value
  }
  if (search.value.trim()) {
    params.q = search.value.trim()
  }

  const response = await apiClient.get('/api/appointments/', { params })
  const data = response.data as PaginatedResponse<AppointmentItem> | AppointmentItem[]
  if (Array.isArray(data)) {
    appointments.value = data
    totalCount.value = data.length
    return
  }
  appointments.value = data.results
  totalCount.value = data.count
}

const fetchDoctors = async () => {
  const response = await apiClient.get('/api/auth/doctors/')
  doctors.value = response.data
}

const fetchPatients = async () => {
  const response = await apiClient.get('/api/auth/patients/')
  patients.value = response.data
}

const fetchScheduleSlots = async () => {
  const response = await apiClient.get('/api/schedule-slots/')
  scheduleSlots.value = response.data
}

const loadPageData = async () => {
  loading.value = true
  try {
    await Promise.all([fetchAppointments(), fetchDoctors(), fetchPatients(), fetchScheduleSlots()])
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Failed to load appointment data')
  } finally {
    loading.value = false
  }
}

const applyListFilters = async () => {
  page.value = 1
  await fetchAppointments()
}

const resetListFilters = async () => {
  search.value = ''
  status.value = 'all'
  page.value = 1
  await fetchAppointments()
}

const handlePageChange = async (newPage: number) => {
  page.value = newPage
  await fetchAppointments()
}

const handleSizeChange = async (newSize: number) => {
  pageSize.value = newSize as 10 | 20 | 50
  page.value = 1
  await fetchAppointments()
}

const openCreateWithPrefill = (prefill?: { patientId?: number; doctorId?: number }) => {
  const firstDoctorId = doctors.value[0]?.id || null
  const patientId = authStore.isPatient ? authStore.user?.id || null : prefill?.patientId || null
  form.value = {
    patient: patientId,
    doctor: prefill?.doctorId || firstDoctorId,
    date: toLocalDateString(new Date()),
    time: '',
    reason: '',
  }
  createSubmitAttempted.value = false
  showDialog.value = true
}

const openCreate = () => openCreateWithPrefill()

const applyCreateQueryPrefill = () => {
  if (route.path !== '/appointments') return
  if (route.query.create !== '1') return
  const patientId = Number(route.query.patientId)
  const doctorId = Number(route.query.doctorId)
  openCreateWithPrefill({
    patientId: Number.isFinite(patientId) ? patientId : undefined,
    doctorId: Number.isFinite(doctorId) ? doctorId : undefined,
  })
  router.replace({ path: '/appointments' })
}

const toApiTime = (time: string) => `${time}:00`

const createAppointment = async () => {
  createSubmitAttempted.value = true
  if (!form.value.patient || !form.value.doctor || !form.value.date || !form.value.time) return
  if (isBlocked(form.value.doctor, form.value.date, form.value.time)) return

  try {
    await apiClient.post('/api/appointments/', {
      patient: form.value.patient,
      doctor: form.value.doctor,
      appointment_date: form.value.date,
      appointment_time: toApiTime(form.value.time),
      reason: form.value.reason,
    })
    showDialog.value = false
    createSubmitAttempted.value = false
    ElMessage.success('Appointment created')
    await fetchAppointments()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Create appointment failed')
  }
}

const openConfirmDialog = (id: number) => {
  const current = appointments.value.find((item) => item.id === id)
  if (!current || !canConfirm(current)) return
  confirmTargetId.value = id
  confirmInfoForm.value = current.confirm_info || ''
  showConfirmDialog.value = true
}

const submitConfirm = async () => {
  if (!confirmTargetId.value) return
  const current = appointments.value.find((item) => item.id === confirmTargetId.value)
  if (!current || !canConfirm(current)) return
  const trimmed = confirmInfoForm.value.trim()
  if (!trimmed || trimmed.length > 500) return

  try {
    await apiClient.put(`/api/appointments/${confirmTargetId.value}/confirm/`, {
      confirm_info: trimmed,
    })
    showConfirmDialog.value = false
    confirmTargetId.value = null
    confirmInfoForm.value = ''
    ElMessage.success('Appointment confirmed')
    await fetchAppointments()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Confirm appointment failed')
  }
}

const openCompleteDialog = (id: number) => {
  const current = appointments.value.find((item) => item.id === id)
  if (!current || !canComplete(current)) return
  completeTargetId.value = id
  completeForm.value = {
    diagnosisResult: current.diagnosis_result || '',
    treatmentPlan: current.treatment_plan || '',
    medicalAdvice: current.medical_advice || '',
    createNextAppointment: false,
    attachments: [],
  }
  completeSubmitAttempted.value = false
  showCompleteDialog.value = true
}

const processCompleteAttachments = async (files: File[]) => {
  if (files.length === 0) return

  try {
    for (const file of files) {
      const validation = validateImageFile(file)
      if (!validation.valid) {
        ElMessage.error(validation.error || 'Invalid image file')
        continue
      }

      const compressed = await compressImage(file)
      completeForm.value.attachments.push({
        file_name: file.name,
        image_data: compressed.base64,
        image_type: file.type || 'image/jpeg',
        compressed_size: compressed.compressedSize,
      })
    }
  } catch {
    ElMessage.error('Attachment processing failed')
  }
}

const onCompleteAttachmentChange = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files || [])
  await processCompleteAttachments(files)
  input.value = ''
}

const openCompleteAttachmentPicker = () => {
  completeAttachmentInputRef.value?.click()
}

const onCompleteUploaderDrop = async (event: DragEvent) => {
  completeUploaderDragging.value = false
  const files = Array.from(event.dataTransfer?.files || [])
  await processCompleteAttachments(files)
}

const removeCompleteAttachment = (index: number) => {
  completeForm.value.attachments = completeForm.value.attachments.filter((_, i) => i !== index)
}

const submitComplete = async () => {
  completeSubmitAttempted.value = true
  if (!completeTargetId.value || completeFormInvalid.value) return
  const current = appointments.value.find((item) => item.id === completeTargetId.value)
  if (!current || !canComplete(current)) return

  const shouldCreateNext = completeForm.value.createNextAppointment
  const nextPatientId = current.patient
  const nextDoctorId = current.doctor

  try {
    await apiClient.put(`/api/appointments/${completeTargetId.value}/complete/`, {
      diagnosis_result: completeForm.value.diagnosisResult.trim(),
      treatment_plan: completeForm.value.treatmentPlan.trim(),
      medical_advice: completeForm.value.medicalAdvice.trim(),
      attachments: completeForm.value.attachments,
    })

    showCompleteDialog.value = false
    completeTargetId.value = null
    completeSubmitAttempted.value = false
    completeForm.value = {
      diagnosisResult: '',
      treatmentPlan: '',
      medicalAdvice: '',
      createNextAppointment: false,
      attachments: [],
    }
    ElMessage.success('Appointment completed')
    await fetchAppointments()

    if (shouldCreateNext) {
      router.push({
        path: '/appointments',
        query: { create: '1', patientId: String(nextPatientId), doctorId: String(nextDoctorId) },
      })
    }
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Complete appointment failed')
  }
}

const openCancelDialog = (id: number) => {
  const target = appointments.value.find((item) => item.id === id)
  if (!target || target.status !== 'pending') return
  cancelTargetId.value = id
  showCancelDialog.value = true
}

const closeCancelDialog = () => {
  showCancelDialog.value = false
  cancelTargetId.value = null
}

const cancelAppointment = async () => {
  if (!cancelTargetId.value) return
  try {
    await apiClient.put(`/api/appointments/${cancelTargetId.value}/cancel/`, {})
    showCancelDialog.value = false
    cancelTargetId.value = null
    ElMessage.success('Appointment cancelled')
    await fetchAppointments()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || 'Cancel appointment failed')
  }
}

onMounted(async () => {
  await loadPageData()
  applyCreateQueryPrefill()
})

watch([status, pageSize], async () => {
  page.value = 1
  await fetchAppointments()
})

watch(
  () => route.query,
  () => applyCreateQueryPrefill()
)
</script>

<template>
  <div class="page">
    <section class="toolbar">
      <div>
        <h2>Appointments</h2>
        <p>Limited slots: 08:00-11:30 and 14:00-17:00 (every 30 minutes).</p>
      </div>
      <ElButton type="primary" @click="openCreate">+ New Appointment</ElButton>
    </section>

    <section class="filters appointments-filters">
      <ElInput
        v-model="search"
        placeholder="Search patient/doctor/reason"
        clearable
        style="width: 280px;"
        @keyup.enter="applyListFilters"
      />
      <ElSelect v-model="status" style="width: 160px;">
        <ElOption label="All status" value="all" />
        <ElOption label="pending" value="pending" />
        <ElOption label="confirmed" value="confirmed" />
        <ElOption label="completed" value="completed" />
        <ElOption label="cancelled" value="cancelled" />
      </ElSelect>
      <ElButton @click="applyListFilters">Search</ElButton>
      <ElButton :disabled="!search && status === 'all'" @click="resetListFilters">Reset</ElButton>
    </section>

    <section class="table-card">
      <ElTable
        v-loading="loading"
        :data="filtered"
        style="width: 100%;"
      >
        <ElTableColumn prop="patient_name" label="Patient" />
        <ElTableColumn prop="doctor_name" label="Doctor" />
        <ElTableColumn label="Date">
          <template #default="{ row }">
            {{ row.appointment_date }} &middot; {{ row.appointment_time.slice(0, 5) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="Status" width="130">
          <template #default="{ row }">
            <ElTag :type="statusTagType(row.status)" size="small">{{ row.status }}</ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="Actions" width="200">
          <template #default="{ row }">
            <template v-if="row.status === 'pending'">
              <ElButton
                text
                :disabled="!canConfirm(row)"
                :title="canConfirm(row) ? '' : 'Only responsible doctor can confirm'"
                @click="openConfirmDialog(row.id)"
              >
                Confirm
              </ElButton>
              <ElButton text type="danger" @click="openCancelDialog(row.id)">Cancel</ElButton>
            </template>
            <template v-else-if="row.status === 'confirmed'">
              <ElButton
                text
                :disabled="!canComplete(row)"
                :title="canComplete(row) ? '' : 'Only responsible doctor can complete'"
                @click="openCompleteDialog(row.id)"
              >
                Complete
              </ElButton>
            </template>
          </template>
        </ElTableColumn>
        <template #empty>
          <ElEmpty description="No appointments found" />
        </template>
      </ElTable>
    </section>

    <section class="table-card" style="display: flex; justify-content: flex-end; padding: 12px 16px;">
      <ElPagination
        :current-page="page"
        :page-size="pageSize"
        :total="totalCount"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </section>

    <!-- Create Dialog -->
    <ElDialog
      v-model="showDialog"
      title="New Appointment"
      width="600px"
      :before-close="() => { showDialog = false; createSubmitAttempted = false }"
    >
      <ElForm label-position="top">
        <ElFormItem label="Patient" required>
          <ElSelect
            v-model="form.patient"
            placeholder="Select patient"
            style="width: 100%;"
            :class="{ 'is-error': createSubmitAttempted && !form.patient }"
          >
            <ElOption
              v-for="patient in patients"
              :key="patient.id"
              :label="displayName(patient)"
              :value="patient.id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="Doctor" required>
          <ElSelect
            v-model="form.doctor"
            placeholder="Select doctor"
            style="width: 100%;"
            :class="{ 'is-error': createSubmitAttempted && !form.doctor }"
          >
            <ElOption
              v-for="doctor in doctors"
              :key="doctor.id"
              :label="displayName(doctor)"
              :value="doctor.id"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="Date" required>
          <ElDatePicker
            v-model="form.date"
            type="date"
            placeholder="Pick a date"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
            :class="{ 'is-error': createSubmitAttempted && !form.date }"
          />
        </ElFormItem>
        <ElFormItem label="Time Slot" required>
          <ElSelect
            v-model="form.time"
            placeholder="Select time slot"
            style="width: 100%;"
            :class="{ 'is-error': createSubmitAttempted && !form.time }"
          >
            <ElOption
              v-for="slot in slotOptions"
              :key="slot.time"
              :label="slot.label"
              :value="slot.time"
              :disabled="slot.blocked"
            />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="Reason">
          <ElInput v-model="form.reason" type="textarea" :rows="3" placeholder="Reason" />
        </ElFormItem>
      </ElForm>

      <div class="slot-hint-card">
        <p>Booked count by time for selected doctor/date</p>
        <ul>
          <li v-for="slot in slotOptions" :key="slot.time">
            <span>{{ slot.time }}</span>
            <span>{{ slot.blocked ? 'Unavailable by schedule' : `${slot.booked} booked` }}</span>
          </li>
        </ul>
      </div>

      <template #footer>
        <ElButton @click="showDialog = false; createSubmitAttempted = false">Cancel</ElButton>
        <ElButton type="primary" @click="createAppointment">Create</ElButton>
      </template>
    </ElDialog>

    <!-- Confirm Dialog -->
    <ElDialog
      v-model="showConfirmDialog"
      title="Confirm Appointment"
      width="520px"
    >
      <p style="margin-bottom: 12px; color: var(--el-text-color-secondary);">
        Record preliminary diagnosis as Confirm Info (max 500 chars).
      </p>
      <ElInput
        v-model="confirmInfoForm"
        type="textarea"
        :rows="4"
        maxlength="500"
        show-word-limit
        placeholder="Enter preliminary diagnosis..."
      />
      <template #footer>
        <ElButton @click="showConfirmDialog = false">Cancel</ElButton>
        <ElButton
          type="primary"
          :disabled="!confirmInfoForm.trim() || confirmInfoTooLong"
          @click="submitConfirm"
        >
          Submit Confirm
        </ElButton>
      </template>
    </ElDialog>

    <!-- Complete Dialog -->
    <ElDialog
      v-model="showCompleteDialog"
      title="Complete Appointment"
      width="620px"
      :before-close="() => { showCompleteDialog = false; completeSubmitAttempted = false }"
    >
      <p style="margin-bottom: 12px; color: var(--el-text-color-secondary);">
        Diagnosis Result and Treatment Plan are required.
      </p>
      <ElForm label-position="top">
        <ElFormItem label="Diagnosis Result" required>
          <ElInput
            v-model="completeForm.diagnosisResult"
            type="textarea"
            :rows="3"
            placeholder="Enter diagnosis result"
            :class="{ 'is-error': completeSubmitAttempted && !completeForm.diagnosisResult.trim() }"
          />
        </ElFormItem>
        <ElFormItem label="Treatment Plan" required>
          <ElInput
            v-model="completeForm.treatmentPlan"
            type="textarea"
            :rows="3"
            placeholder="Enter treatment plan"
            :class="{ 'is-error': completeSubmitAttempted && !completeForm.treatmentPlan.trim() }"
          />
        </ElFormItem>
        <ElFormItem label="Medical Advice">
          <ElInput
            v-model="completeForm.medicalAdvice"
            type="textarea"
            :rows="3"
            placeholder="Enter medical advice"
          />
        </ElFormItem>
        <ElFormItem label="Attachments (image)">
          <div class="complete-attachment-area">
            <div
              class="file-uploader"
              :class="{ dragging: completeUploaderDragging }"
              role="button"
              tabindex="0"
              @click="openCompleteAttachmentPicker"
              @keydown.enter.prevent="openCompleteAttachmentPicker"
              @dragover.prevent="completeUploaderDragging = true"
              @dragleave.prevent="completeUploaderDragging = false"
              @drop.prevent="onCompleteUploaderDrop"
            >
              <input
                ref="completeAttachmentInputRef"
                type="file"
                accept="image/*"
                multiple
                class="hidden-file-input"
                @change="onCompleteAttachmentChange"
              />
              <span class="file-uploader-icon">&#x2B06;</span>
              <div>
                <p class="file-uploader-title">Upload attachments</p>
                <p class="file-uploader-subtitle">Images only, auto-compressed before submit</p>
              </div>
            </div>
            <p v-if="showSqliteAttachmentHint" style="margin: 4px 0 0; color: var(--el-text-color-secondary); font-size: 12px;">
              Current environment is development (SQLite). Attachment submission will not take effect.
            </p>
            <ul v-if="completeForm.attachments.length > 0" class="complete-attachment-list">
              <li v-for="(item, index) in completeForm.attachments" :key="`${item.file_name}-${index}`">
                <span>{{ item.file_name }} &middot; {{ item.compressed_size }}KB</span>
                <ElButton text type="danger" size="small" @click="removeCompleteAttachment(index)">Remove</ElButton>
              </li>
            </ul>
          </div>
        </ElFormItem>
        <ElFormItem>
          <ElCheckbox v-model="completeForm.createNextAppointment">
            Create next appointment after submit
          </ElCheckbox>
        </ElFormItem>
      </ElForm>
      <template #footer>
        <ElButton @click="showCompleteDialog = false; completeSubmitAttempted = false">Cancel</ElButton>
        <ElButton type="primary" @click="submitComplete">Submit Complete</ElButton>
      </template>
    </ElDialog>

    <!-- Cancel Dialog -->
    <ElDialog
      v-model="showCancelDialog"
      title="Cancel Appointment"
      width="460px"
      :before-close="closeCancelDialog"
    >
      <p style="color: var(--el-color-danger);">{{ cancelDialogMessage }}</p>
      <template #footer>
        <ElButton @click="closeCancelDialog">Keep Appointment</ElButton>
        <ElButton type="danger" @click="cancelAppointment">Confirm Cancel</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<style scoped>
.slot-hint-card {
  margin-top: 8px;
  padding: 12px;
  background: var(--el-fill-color-light, #f5f7fa);
  border-radius: 4px;
  font-size: 13px;
}
.slot-hint-card ul {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 4px;
}
.slot-hint-card li {
  display: flex;
  justify-content: space-between;
  padding: 2px 0;
}
.complete-attachment-area {
  width: 100%;
}
.file-uploader {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 2px dashed var(--el-border-color, #dcdfe6);
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.file-uploader:hover,
.file-uploader.dragging {
  border-color: var(--el-color-primary);
}
.file-uploader-icon {
  font-size: 24px;
}
.file-uploader-title {
  font-weight: 500;
  margin: 0;
}
.file-uploader-subtitle {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin: 2px 0 0;
}
.hidden-file-input {
  display: none;
}
.complete-attachment-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
.complete-attachment-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}
</style>
