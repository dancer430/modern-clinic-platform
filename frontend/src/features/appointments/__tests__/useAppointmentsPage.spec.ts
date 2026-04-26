import { describe, it, expect, beforeEach, vi } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createRouter, createMemoryHistory, type Router } from 'vue-router'

vi.mock('@/shared/http', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  httpClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
  registerHttpAuthHandlers: vi.fn(),
  clearHttpAuthHandlers: vi.fn(),
  getHttpAuthHandlers: vi.fn(),
}))

vi.mock('@/utils/imageUtils', () => ({
  validateImageFile: vi.fn(),
  compressImage: vi.fn(),
}))

vi.mock('../api', () => ({
  fetchAppointmentsRequest: vi.fn(),
  fetchDoctorsRequest: vi.fn(),
  fetchPatientsRequest: vi.fn(),
  fetchScheduleSlotsRequest: vi.fn(),
  createAppointmentRequest: vi.fn(),
  confirmAppointmentRequest: vi.fn(),
  completeAppointmentRequest: vi.fn(),
  cancelAppointmentRequest: vi.fn(),
}))

import {
  fetchAppointmentsRequest,
  fetchDoctorsRequest,
  fetchPatientsRequest,
  fetchScheduleSlotsRequest,
} from '../api'
import { useAuthStore } from '@/features/auth'
import { useAppointmentsPage } from '../composables/useAppointmentsPage'
import type { AppointmentItem, ScheduleSlot, UserOption } from '../types'

type ComposableApi = ReturnType<typeof useAppointmentsPage>

const sampleDoctor: UserOption = { id: 1, username: 'doc', name: 'Dr One', user_type: 'doctor' }
const samplePatient: UserOption = { id: 2, username: 'pat', name: 'Pat Two', user_type: 'patient' }

const createTestRouter = (): Router =>
  createRouter({
    history: createMemoryHistory('/appointments'),
    routes: [
      { path: '/appointments', name: 'appointments', component: { template: '<div/>' } },
      { path: '/', component: { template: '<div/>' } },
    ],
  })

const setupComposable = async (overrides: {
  appointments?: AppointmentItem[]
  doctors?: UserOption[]
  patients?: UserOption[]
  scheduleSlots?: ScheduleSlot[]
}) => {
  vi.mocked(fetchAppointmentsRequest).mockResolvedValue(overrides.appointments ?? [])
  vi.mocked(fetchDoctorsRequest).mockResolvedValue(overrides.doctors ?? [sampleDoctor])
  vi.mocked(fetchPatientsRequest).mockResolvedValue(overrides.patients ?? [samplePatient])
  vi.mocked(fetchScheduleSlotsRequest).mockResolvedValue(overrides.scheduleSlots ?? [])

  const router = createTestRouter()
  await router.push('/appointments')
  await router.isReady()

  let api!: ComposableApi
  const Host = defineComponent({
    setup() {
      api = useAppointmentsPage()
      return () => h('div')
    },
  })

  mount(Host, { global: { plugins: [router] } })
  await flushPromises()
  await nextTick()
  return api
}

describe('useAppointmentsPage', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.user = {
      id: 99,
      username: 'admin',
      email: 'a@x',
      name: 'Admin',
      user_type: 'admin',
      phone: '',
    }
    auth.token = 'tok'
    vi.clearAllMocks()
  })

  it('returns empty slot options when no doctor is selected', async () => {
    const api = await setupComposable({})
    api.form.value.doctor = null
    await nextTick()
    expect(api.slotOptions.value).toEqual([])
  })

  it('marks blocked slots as unavailable in slotOptions', async () => {
    const slotDate = '2026-05-01'
    const blocked: ScheduleSlot = {
      doctor: sampleDoctor.id,
      slot_date: slotDate,
      slot_time: '09:00:00',
      is_available: false,
    }
    const api = await setupComposable({ scheduleSlots: [blocked] })
    api.form.value.doctor = sampleDoctor.id
    api.form.value.date = slotDate
    await nextTick()

    const nineAm = api.slotOptions.value.find((opt) => opt.time === '09:00')
    expect(nineAm?.blocked).toBe(true)
    expect(nineAm?.label).toContain('unavailable')

    const tenAm = api.slotOptions.value.find((opt) => opt.time === '10:00')
    expect(tenAm?.blocked).toBe(false)
    expect(tenAm?.booked).toBe(0)
  })

  it('counts non-cancelled appointments as booked for the same doctor/date/time', async () => {
    const slotDate = '2026-05-02'
    const appointments: AppointmentItem[] = [
      {
        id: 1,
        patient: samplePatient.id,
        patient_name: 'Pat',
        doctor: sampleDoctor.id,
        doctor_name: 'Dr',
        appointment_date: slotDate,
        appointment_time: '10:00:00',
        reason: '',
        status: 'pending',
        confirm_info: '',
        diagnosis_result: '',
        treatment_plan: '',
        medical_advice: '',
      },
      {
        id: 2,
        patient: samplePatient.id,
        patient_name: 'Pat',
        doctor: sampleDoctor.id,
        doctor_name: 'Dr',
        appointment_date: slotDate,
        appointment_time: '10:00:00',
        reason: '',
        status: 'cancelled',
        confirm_info: '',
        diagnosis_result: '',
        treatment_plan: '',
        medical_advice: '',
      },
    ]
    const api = await setupComposable({ appointments })
    api.form.value.doctor = sampleDoctor.id
    api.form.value.date = slotDate
    await nextTick()

    const tenAm = api.slotOptions.value.find((opt) => opt.time === '10:00')
    expect(tenAm?.booked).toBe(1)
    expect(tenAm?.label).toContain('1 booked')
  })

  it('maps appointment status to the correct Element Plus tag type', async () => {
    const api = await setupComposable({})
    expect(api.statusTagType('pending')).toBe('warning')
    expect(api.statusTagType('confirmed')).toBe('')
    expect(api.statusTagType('completed')).toBe('success')
    expect(api.statusTagType('cancelled')).toBe('danger')
  })
})
