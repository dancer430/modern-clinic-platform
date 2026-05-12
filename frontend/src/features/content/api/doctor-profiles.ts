import api from '@/shared/http/client'
import type {
  AssignmentItem,
  DoctorPortalCard,
  DoctorPortalDetail,
  DoctorProfileAdmin,
  DoctorProfileSelf,
} from '../types'

export const portalDoctorsApi = {
  list(departmentSlug?: string): Promise<DoctorPortalCard[]> {
    return api
      .get<DoctorPortalCard[]>('/api/portal/doctors/', {
        params: departmentSlug ? { department: departmentSlug } : {},
      })
      .then((r) => r.data)
  },
  detail(userId: number): Promise<DoctorPortalDetail> {
    return api.get<DoctorPortalDetail>(`/api/portal/doctors/${userId}/`).then((r) => r.data)
  },
}

export const adminDoctorProfilesApi = {
  list(): Promise<DoctorProfileAdmin[]> {
    return api.get<DoctorProfileAdmin[]>('/api/admin/content/doctor-profiles/').then((r) => r.data)
  },
  detail(userId: number): Promise<DoctorProfileAdmin> {
    return api
      .get<DoctorProfileAdmin>(`/api/admin/content/doctor-profiles/${userId}/`)
      .then((r) => r.data)
  },
  update(userId: number, payload: Partial<DoctorProfileAdmin>): Promise<DoctorProfileAdmin> {
    return api
      .put<DoctorProfileAdmin>(`/api/admin/content/doctor-profiles/${userId}/`, payload)
      .then((r) => r.data)
  },
  setDepartments(userId: number, items: AssignmentItem[]): Promise<DoctorProfileAdmin> {
    return api
      .put<DoctorProfileAdmin>(
        `/api/admin/content/doctor-profiles/${userId}/departments/`,
        items,
      )
      .then((r) => r.data)
  },
  approve(userId: number): Promise<DoctorProfileAdmin> {
    return api
      .post<DoctorProfileAdmin>(`/api/admin/content/doctor-profiles/${userId}/approve/`)
      .then((r) => r.data)
  },
  reject(userId: number, note: string): Promise<DoctorProfileAdmin> {
    return api
      .post<DoctorProfileAdmin>(`/api/admin/content/doctor-profiles/${userId}/reject/`, { note })
      .then((r) => r.data)
  },
  pendingReviews(): Promise<DoctorProfileAdmin[]> {
    return api
      .get<DoctorProfileAdmin[]>('/api/admin/content/pending-reviews/')
      .then((r) => r.data)
  },
}

export const doctorSelfApi = {
  me(): Promise<DoctorProfileSelf> {
    return api.get<DoctorProfileSelf>('/api/doctor/content/profile/me/').then((r) => r.data)
  },
  save(payload: Partial<DoctorProfileSelf>): Promise<DoctorProfileSelf> {
    return api.put<DoctorProfileSelf>('/api/doctor/content/profile/me/', payload).then((r) => r.data)
  },
  submitReview(): Promise<DoctorProfileSelf> {
    return api
      .post<DoctorProfileSelf>('/api/doctor/content/profile/me/submit-review/')
      .then((r) => r.data)
  },
}
