import { computed, type Ref } from 'vue'
import type { DoctorProfileSelf } from '../types'

export function useDraftReview(profile: Ref<DoctorProfileSelf | null>) {
  const isLocked = computed(() => profile.value?.draft_status === 'pending')
  const canSubmit = computed(() => profile.value?.draft_status === 'none')
  const wasRejected = computed(() => profile.value?.draft_status === 'rejected')
  const wasApproved = computed(() => profile.value?.draft_status === 'approved')
  return { isLocked, canSubmit, wasRejected, wasApproved }
}
