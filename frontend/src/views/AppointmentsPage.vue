<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
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
const errorMessage = ref('')

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
      label: blocked ? `${time} · unavailable` : `${time} · ${booked} booked`,
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
  errorMessage.value = ''
  try {
    await Promise.all([fetchAppointments(), fetchDoctors(), fetchPatients(), fetchScheduleSlots()])
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Failed to load appointment data'
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

const goPrevPage = async () => {
  if (page.value <= 1) return
  page.value -= 1
  await fetchAppointments()
}

const goNextPage = async () => {
  if (page.value >= totalPages.value) return
  page.value += 1
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
    await fetchAppointments()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Create appointment failed'
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
    await fetchAppointments()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Confirm appointment failed'
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
        errorMessage.value = validation.error || 'Invalid image file'
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
    errorMessage.value = 'Attachment processing failed'
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
    await fetchAppointments()

    if (shouldCreateNext) {
      router.push({
        path: '/appointments',
        query: { create: '1', patientId: String(nextPatientId), doctorId: String(nextDoctorId) },
      })
    }
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Complete appointment failed'
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
    await fetchAppointments()
  } catch (error: any) {
    errorMessage.value = error.response?.data?.detail || 'Cancel appointment failed'
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
      <button class="primary" @click="openCreate">+ New Appointment</button>
    </section>

    <section v-if="errorMessage" class="table-card" style="padding: 10px 12px; color: #c2334a;">
      {{ errorMessage }}
    </section>

    <section class="filters appointments-filters">
      <input v-model="search" placeholder="Search patient/doctor/reason" @keyup.enter="applyListFilters" />
      <select v-model="status">
        <option value="all">All status</option>
        <option value="pending">pending</option>
        <option value="confirmed">confirmed</option>
        <option value="completed">completed</option>
        <option value="cancelled">cancelled</option>
      </select>
      <div class="tabs">
        <button class="ghost" @click="applyListFilters">Search</button>
        <button class="ghost" :disabled="!search && status === 'all'" @click="resetListFilters">Reset</button>
      </div>
    </section>

    <section class="table-card">
      <table>
        <thead>
          <tr>
            <th>Patient</th>
            <th>Doctor</th>
            <th>Date</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in filtered" :key="item.id">
            <td>{{ item.patient_name }}</td>
            <td>{{ item.doctor_name }}</td>
            <td>{{ item.appointment_date }} · {{ item.appointment_time.slice(0, 5) }}</td>
            <td><span class="badge" :class="item.status">{{ item.status }}</span></td>
            <td class="actions-cell">
              <template v-if="item.status === 'pending'">
                <button
                  class="ghost action-btn"
                  :disabled="!canConfirm(item)"
                  :title="canConfirm(item) ? '' : 'Only responsible doctor can confirm'"
                  @click="openConfirmDialog(item.id)"
                >
                  Confirm
                </button>
                <button class="danger action-btn" @click="openCancelDialog(item.id)">Cancel</button>
              </template>
              <template v-else-if="item.status === 'confirmed'">
                <button
                  class="ghost action-btn"
                  :disabled="!canComplete(item)"
                  :title="canComplete(item) ? '' : 'Only responsible doctor can complete'"
                  @click="openCompleteDialog(item.id)"
                >
                  Complete
                </button>
              </template>
            </td>
          </tr>
        </tbody>
      </table>
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

    <div v-if="showDialog" class="overlay" @click.self="showDialog = false; createSubmitAttempted = false">
      <div class="dialog">
        <h3>New Appointment</h3>
        <div class="grid">
          <select v-model.number="form.patient" :class="{ 'input-invalid': createSubmitAttempted && !form.patient }">
            <option :value="null">Select patient</option>
            <option v-for="patient in patients" :key="patient.id" :value="patient.id">{{ displayName(patient) }}</option>
          </select>
          <select v-model.number="form.doctor" :class="{ 'input-invalid': createSubmitAttempted && !form.doctor }">
            <option :value="null">Select doctor</option>
            <option v-for="doctor in doctors" :key="doctor.id" :value="doctor.id">{{ displayName(doctor) }}</option>
          </select>
          <input v-model="form.date" type="date" :class="{ 'input-invalid': createSubmitAttempted && !form.date }" />
          <select v-model="form.time" :class="{ 'input-invalid': createSubmitAttempted && !form.time }">
            <option value="">Select time slot</option>
            <option v-for="slot in slotOptions" :key="slot.time" :value="slot.time" :disabled="slot.blocked">
              {{ slot.label }}
            </option>
          </select>
          <textarea v-model="form.reason" placeholder="Reason"></textarea>
        </div>

        <div class="slot-hint-card">
          <p>Booked count by time for selected doctor/date</p>
          <ul>
            <li v-for="slot in slotOptions" :key="slot.time">
              <span>{{ slot.time }}</span>
              <span>{{ slot.blocked ? 'Unavailable by schedule' : `${slot.booked} booked` }}</span>
            </li>
          </ul>
        </div>

        <div class="actions">
          <button class="ghost" @click="showDialog = false; createSubmitAttempted = false">Cancel</button>
          <button class="primary" @click="createAppointment">Create</button>
        </div>
      </div>
    </div>

    <div v-if="showConfirmDialog" class="overlay" @click.self="showConfirmDialog = false">
      <div class="dialog">
        <h3>Confirm Appointment</h3>
        <p class="dialog-tip">Record preliminary diagnosis as Confirm Info (max 500 chars).</p>
        <textarea v-model="confirmInfoForm" class="confirm-info-input" maxlength="500" placeholder="Enter preliminary diagnosis..."></textarea>
        <div class="confirm-info-footer">
          <span :class="{ 'danger-text': confirmInfoTooLong }">{{ confirmInfoForm.length }}/500</span>
        </div>
        <div class="actions">
          <button class="ghost" @click="showConfirmDialog = false">Cancel</button>
          <button class="primary" :disabled="!confirmInfoForm.trim() || confirmInfoTooLong" @click="submitConfirm">Submit Confirm</button>
        </div>
      </div>
    </div>

    <div v-if="showCompleteDialog" class="overlay" @click.self="showCompleteDialog = false; completeSubmitAttempted = false">
      <div class="dialog">
        <h3>Complete Appointment</h3>
        <p class="dialog-tip">Diagnosis Result and Treatment Plan are required.</p>
        <div class="appointment-complete-form">
          <label class="field-label">Diagnosis Result <span class="required-mark">*</span></label>
          <textarea
            v-model="completeForm.diagnosisResult"
            class="confirm-info-input"
            :class="{ 'input-invalid': completeSubmitAttempted && !completeForm.diagnosisResult.trim() }"
            placeholder="Enter diagnosis result"
          ></textarea>

          <label class="field-label">Treatment Plan <span class="required-mark">*</span></label>
          <textarea
            v-model="completeForm.treatmentPlan"
            class="confirm-info-input"
            :class="{ 'input-invalid': completeSubmitAttempted && !completeForm.treatmentPlan.trim() }"
            placeholder="Enter treatment plan"
          ></textarea>

          <label class="field-label">Medical Advice</label>
          <textarea v-model="completeForm.medicalAdvice" class="confirm-info-input" placeholder="Enter medical advice"></textarea>

          <label class="field-label">Attachments (image)</label>
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
              <span class="file-uploader-icon">⬆</span>
              <div>
                <p class="file-uploader-title">Upload attachments</p>
                <p class="file-uploader-subtitle">Images only, auto-compressed before submit</p>
              </div>
            </div>
            <p v-if="showSqliteAttachmentHint" class="dialog-tip" style="margin: 4px 0 0;">
              Current environment is development (SQLite). Attachment submission will not take effect.
            </p>
            <ul v-if="completeForm.attachments.length > 0" class="complete-attachment-list">
              <li v-for="(item, index) in completeForm.attachments" :key="`${item.file_name}-${index}`">
                <span>{{ item.file_name }} · {{ item.compressed_size }}KB</span>
                <button type="button" class="ghost" @click="removeCompleteAttachment(index)">Remove</button>
              </li>
            </ul>
          </div>

          <div class="next-appointment-row">
            <label class="checkbox-label">
              <input v-model="completeForm.createNextAppointment" type="checkbox" />
              Create next appointment after submit
            </label>
          </div>
        </div>
        <div class="actions">
          <button class="ghost" @click="showCompleteDialog = false; completeSubmitAttempted = false">Cancel</button>
          <button class="primary" @click="submitComplete">Submit Complete</button>
        </div>
      </div>
    </div>

    <div v-if="showCancelDialog" class="overlay" @click.self="closeCancelDialog">
      <div class="dialog" style="max-width: 460px;">
        <h3>Cancel Appointment</h3>
        <p class="dialog-tip danger-text">{{ cancelDialogMessage }}</p>
        <div class="actions">
          <button class="ghost" @click="closeCancelDialog">Keep Appointment</button>
          <button class="danger" @click="cancelAppointment">Confirm Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>
