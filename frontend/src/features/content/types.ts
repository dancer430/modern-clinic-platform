export interface DepartmentCard {
  id: number
  slug: string
  name: string
  summary: string
  cover_image_url: string | null
  display_order: number
}

export interface DepartmentDetail extends DepartmentCard {
  description_html: string
}

export interface DepartmentAdminInput {
  name: string
  slug: string
  summary?: string
  description_html?: string
  display_order?: number
  is_published?: boolean
}

export interface DoctorDepartmentLink {
  slug: string
  name: string
  is_primary: boolean
}

export interface DoctorPortalCard {
  user_id: number
  name: string
  title: string
  specialty: string
  cover_image_url: string | null
  departments: DoctorDepartmentLink[]
}

export interface DoctorPortalDetail extends DoctorPortalCard {
  bio_published_html: string
}

export type DraftStatus = 'none' | 'pending' | 'approved' | 'rejected'

export interface DoctorProfileSelf {
  title: string
  specialty: string
  bio_published_html: string
  bio_draft_html: string
  cover_image_url: string | null
  is_published: boolean
  draft_status: DraftStatus
  draft_submitted_at: string | null
  draft_reviewed_at: string | null
  draft_review_note: string
  departments: DoctorDepartmentLink[]
}

export interface DoctorProfileAdmin extends DoctorProfileSelf {
  user_id: number
  username: string
  name: string
}

export interface AssignmentItem {
  department_id: number
  is_primary: boolean
}
