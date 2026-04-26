export type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled'

export interface AppointmentAttachmentItem {
  id: number
  file_name: string
  image_data: string
  image_type: string
  compressed_size: number
  created_at: string
}

export interface AppointmentItem {
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
  attachments?: AppointmentAttachmentItem[]
}

export interface CompleteAttachmentItem {
  file_name: string
  image_data: string
  image_type: string
  compressed_size: number
}

export interface UserOption {
  id: number
  username: string
  name: string
  user_type: 'admin' | 'doctor' | 'patient'
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export interface ScheduleSlot {
  doctor: number
  slot_date: string
  slot_time: string
  is_available: boolean
}

export interface CreateAppointmentForm {
  patient: number | null
  doctor: number | null
  date: string
  time: string
  reason: string
}

export interface CompleteAppointmentForm {
  diagnosisResult: string
  treatmentPlan: string
  medicalAdvice: string
  createNextAppointment: boolean
  attachments: CompleteAttachmentItem[]
}

export interface AppointmentQueryParams {
  page: number
  page_size: number
  status?: AppointmentStatus
  q?: string
}

export const SLOT_TIMES = [
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
] as const

export const toLocalDateString = (date: Date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export const toApiTime = (time: string) => `${time}:00`
