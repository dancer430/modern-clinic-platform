import { computed, ref } from 'vue'
import apiClient from '@/utils/apiClient'

interface PlatformSetting {
  platform_name: string
  logo_data?: string
}

const platformName = ref('MediNexus')
const logoData = ref('')
const loaded = ref(false)

export const usePlatformBrand = () => {
  const loadPlatformBrand = async (force = false) => {
    if (loaded.value && !force) return
    try {
      const response = await apiClient.get('/api/auth/platform/')
      const data = response.data as PlatformSetting
      platformName.value = data.platform_name || 'MediNexus'
      logoData.value = data.logo_data || ''
      loaded.value = true
    } catch {
      if (!loaded.value) {
        platformName.value = 'MediNexus'
        logoData.value = ''
      }
    }
  }

  return {
    platformName,
    logoData,
    hasCustomLogo: computed(() => !!logoData.value),
    loadPlatformBrand,
  }
}
