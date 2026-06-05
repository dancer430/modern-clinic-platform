import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import { useAuthStore } from '@/features/auth'
import { compressImage, validateImageFile } from '@/utils/imageUtils'

import {
  cancelAppointmentRequest,
  completeAppointmentRequest,
  confirmAppointmentRequest,
  createAppointmentRequest,
  fetchAppointmentsRequest,
  fetchDoctorsRequest,
  fetchPatientsRequest,
  fetchScheduleSlotsRequest,
} from '../api'
import type {
  AppointmentItem,
  AppointmentQueryParams,
  AppointmentStatus,
  CompleteAppointmentForm,
  CreateAppointmentForm,
  ScheduleSlot,
  UserOption,
} from '../types'
import { SLOT_TIMES, toApiTime, toLocalDateString } from '../types'

const createDefaultForm = (): CreateAppointmentForm => ({
  patient: null,
  doctor: null,
  date: toLocalDateString(new Date()),
  time: '',
  reason: '',
})

const createDefaultCompleteForm = (): CompleteAppointmentForm => ({
  diagnosisResult: '',
  treatmentPlan: '',
  medicalAdvice: '',
  createNextAppointment: false,
  attachments: [],
})

export const useAppointmentsPage = () => {
  const authStore = useAuthStore()
  const route = useRoute()
  const router = useRouter()

  const loading = ref(false)

  const appointments = ref<AppointmentItem[]>([])
  const doctors = ref<UserOption[]>([])
  const patients = ref<UserOption[]>([])
  const scheduleSlots = ref<ScheduleSlot[]>([])

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
  const completeForm = ref<CompleteAppointmentForm>(createDefaultCompleteForm())

  const form = ref<CreateAppointmentForm>(createDefaultForm())

  const displayName = (user: UserOption) => user.name?.trim() || user.username

  const filtered = computed(() => appointments.value)
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

      const state: 'available' | 'booked' | 'unavailable' =
        blocked ? 'unavailable' : booked > 0 ? 'booked' : 'available'

      return {
        time,
        blocked,
        booked,
        label: blocked ? `${time} · unavailable` : `${time} · ${booked} booked`,
        state,
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

  const statusTagType = (value: AppointmentStatus) => {
    switch (value) {
      case 'pending':
        return 'warning'
      case 'confirmed':
        return ''
      case 'completed':
        return 'success'
      case 'cancelled':
        return 'danger'
      default:
        return 'info'
    }
  }

  const fetchAppointments = async () => {
    const params: AppointmentQueryParams = {
      page: page.value,
      page_size: pageSize.value,
    }

    if (status.value !== 'all') {
      params.status = status.value
    }

    if (search.value.trim()) {
      params.q = search.value.trim()
    }

    const data = await fetchAppointmentsRequest(params)

    if (Array.isArray(data)) {
      appointments.value = data
      totalCount.value = data.length
      return
    }

    appointments.value = data.results
    totalCount.value = data.count
  }

  const fetchDoctors = async () => {
    doctors.value = await fetchDoctorsRequest()
  }

  const fetchPatients = async () => {
    patients.value = await fetchPatientsRequest()
  }

  const fetchScheduleSlots = async () => {
    scheduleSlots.value = await fetchScheduleSlotsRequest()
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

  const openCreate = () => {
    openCreateWithPrefill()
    if (authStore.user?.user_type === 'doctor') {
      form.value.doctor = authStore.user.id
    }
  }

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

  const createAppointment = async () => {
    createSubmitAttempted.value = true
    if (!form.value.patient || !form.value.doctor || !form.value.date || !form.value.time) return
    if (isBlocked(form.value.doctor, form.value.date, form.value.time)) return

    try {
      await createAppointmentRequest({
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
      await confirmAppointmentRequest(confirmTargetId.value, trimmed)
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
    completeForm.value.attachments = completeForm.value.attachments.filter((_, currentIndex) => currentIndex !== index)
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
      await completeAppointmentRequest(completeTargetId.value, completeForm.value)

      showCompleteDialog.value = false
      completeTargetId.value = null
      completeSubmitAttempted.value = false
      completeForm.value = createDefaultCompleteForm()
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
      await cancelAppointmentRequest(cancelTargetId.value)
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

  return {
    appointments,
    applyListFilters,
    cancelAppointment,
    cancelDialogMessage,
    canComplete,
    canConfirm,
    closeCancelDialog,
    completeAttachmentInputRef,
    completeForm,
    completeFormInvalid,
    completeSubmitAttempted,
    completeTargetId,
    completeUploaderDragging,
    confirmInfoForm,
    confirmInfoTooLong,
    confirmTargetId,
    createAppointment,
    createSubmitAttempted,
    displayName,
    doctors,
    filtered,
    form,
    handlePageChange,
    handleSizeChange,
    loading,
    onCompleteAttachmentChange,
    onCompleteUploaderDrop,
    openCompleteAttachmentPicker,
    openCancelDialog,
    openCompleteDialog,
    openConfirmDialog,
    openCreate,
    page,
    pageEnd,
    pageSize,
    pageStart,
    patients,
    removeCompleteAttachment,
    resetListFilters,
    search,
    showCancelDialog,
    showCompleteDialog,
    showConfirmDialog,
    showDialog,
    showSqliteAttachmentHint,
    slotOptions,
    status,
    statusTagType,
    submitComplete,
    submitConfirm,
    totalCount,
    totalPages,
  }
}
