<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import DoctorCard from '../../components/DoctorCard.vue'
import { portalDoctorsApi } from '../../api/doctor-profiles'
import type { DoctorPortalCard } from '../../types'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const items = ref<DoctorPortalCard[]>([])
const loading = ref(false)
const error = ref<string | null>(null)

const departmentSlug = computed(() => {
  const q = route.query.department
  return typeof q === 'string' ? q : undefined
})

const load = async () => {
  loading.value = true
  error.value = null
  try {
    items.value = await portalDoctorsApi.list(departmentSlug.value)
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="portal-page">
    <header class="portal-page__header">
      <h1>{{ t('portal.doctorList.title') }}</h1>
      <p>{{ t('portal.doctorList.subtitle') }}</p>
    </header>
    <div v-if="loading" class="portal-page__loading">{{ t('portal.loading') }}</div>
    <div v-else-if="error" class="portal-page__error">{{ error }}</div>
    <div v-else class="portal-page__grid">
      <DoctorCard
        v-for="doc in items"
        :key="doc.user_id"
        :doctor="doc"
        @click="router.push(`/portal/doctors/${doc.user_id}`)"
      />
    </div>
  </main>
</template>

<style scoped>
.portal-page { max-width: 1120px; margin: 0 auto; padding: 48px 24px; }
.portal-page__header h1 { margin: 0; font-size: 32px; color: #1f2f4e; }
.portal-page__header p { margin: 8px 0 28px; color: #6f7894; }
.portal-page__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.portal-page__loading, .portal-page__error { padding: 60px 0; text-align: center; color: #6f7894; }
</style>
