import api from '@/shared/http/client'
import type { DepartmentAdminInput, DepartmentCard, DepartmentDetail } from '../types'

export interface PortalDepartmentDetailResponse {
  department: DepartmentDetail
  doctors: Array<{
    user_id: number
    name: string
    title: string
    specialty: string
    cover_image_url: string | null
    departments: Array<{ slug: string; name: string; is_primary: boolean }>
  }>
}

export const portalDepartmentsApi = {
  list(limit?: number): Promise<DepartmentCard[]> {
    return api
      .get<DepartmentCard[]>('/api/portal/departments/', { params: limit ? { limit } : {} })
      .then((r) => r.data)
  },
  detail(slug: string): Promise<PortalDepartmentDetailResponse> {
    return api.get<PortalDepartmentDetailResponse>(`/api/portal/departments/${slug}/`).then((r) => r.data)
  },
}

export const adminDepartmentsApi = {
  list(): Promise<DepartmentCard[]> {
    return api.get<DepartmentCard[]>('/api/admin/content/departments/').then((r) => r.data)
  },
  detail(id: number): Promise<DepartmentDetail> {
    return api.get<DepartmentDetail>(`/api/admin/content/departments/${id}/`).then((r) => r.data)
  },
  create(payload: DepartmentAdminInput): Promise<DepartmentDetail> {
    return api.post<DepartmentDetail>('/api/admin/content/departments/', payload).then((r) => r.data)
  },
  update(id: number, payload: Partial<DepartmentAdminInput>): Promise<DepartmentDetail> {
    return api.put<DepartmentDetail>(`/api/admin/content/departments/${id}/`, payload).then((r) => r.data)
  },
  remove(id: number): Promise<void> {
    return api.delete(`/api/admin/content/departments/${id}/`).then(() => undefined)
  },
}
