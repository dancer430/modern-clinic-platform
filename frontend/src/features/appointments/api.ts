import apiClient from '@/utils/apiClient'

import type {
  AppointmentItem,
  AppointmentQueryParams,
  CompleteAppointmentForm,
  PaginatedResponse,
  ScheduleSlot,
  UserOption,
} from './types'

export const fetchAppointmentsRequest = async (params: AppointmentQueryParams) => {
  const response = await apiClient.get<PaginatedResponse<AppointmentItem> | AppointmentItem[]>('/api/appointments/', {
    params,
  })

  return response.data
}

export const fetchDoctorsRequest = async () => {
  const response = await apiClient.get<UserOption[]>('/api/auth/doctors/')
  return response.data
}

export const fetchPatientsRequest = async () => {
  const response = await apiClient.get<UserOption[]>('/api/auth/patients/')
  return response.data
}

export const fetchScheduleSlotsRequest = async () => {
  const response = await apiClient.get<ScheduleSlot[]>('/api/schedule-slots/')
  return response.data
}

export const createAppointmentRequest = async (payload: {
  patient: number
  doctor: number
  appointment_date: string
  appointment_time: string
  reason: string
}) => {
  await apiClient.post('/api/appointments/', payload)
}

export const confirmAppointmentRequest = async (appointmentId: number, confirmInfo: string) => {
  await apiClient.put(`/api/appointments/${appointmentId}/confirm/`, {
    confirm_info: confirmInfo,
  })
}

export const completeAppointmentRequest = async (
  appointmentId: number,
  payload: Pick<CompleteAppointmentForm, 'diagnosisResult' | 'treatmentPlan' | 'medicalAdvice' | 'attachments'>
) => {
  await apiClient.put(`/api/appointments/${appointmentId}/complete/`, {
    diagnosis_result: payload.diagnosisResult.trim(),
    treatment_plan: payload.treatmentPlan.trim(),
    medical_advice: payload.medicalAdvice.trim(),
    attachments: payload.attachments,
  })
}

export const cancelAppointmentRequest = async (appointmentId: number) => {
  await apiClient.put(`/api/appointments/${appointmentId}/cancel/`, {})
}
