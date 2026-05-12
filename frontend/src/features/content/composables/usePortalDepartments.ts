import { ref } from 'vue'
import { portalDepartmentsApi } from '../api/departments'
import type { DepartmentCard } from '../types'

export function usePortalDepartments() {
  const items = ref<DepartmentCard[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const load = async (limit?: number) => {
    loading.value = true
    error.value = null
    try {
      items.value = await portalDepartmentsApi.list(limit)
    } catch (e) {
      error.value = (e as Error).message ?? 'failed to load departments'
    } finally {
      loading.value = false
    }
  }

  return { items, loading, error, load }
}
