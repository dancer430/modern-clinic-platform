<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DoctorCard from '../../components/DoctorCard.vue'
import { portalDepartmentsApi, type PortalDepartmentDetailResponse } from '../../api/departments'

const route = useRoute()
const router = useRouter()
const data = ref<PortalDepartmentDetailResponse | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const load = async () => {
  loading.value = true
  error.value = null
  try {
    data.value = await portalDepartmentsApi.detail(String(route.params.slug))
    if (data.value?.department.name) {
      document.title = `${data.value.department.name} – Departments`
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.slug, load)
</script>

<template>
  <main class="portal-page" v-if="!loading && data">
    <button class="back" @click="router.push('/portal/departments')">← All departments</button>
    <header class="portal-page__hero">
      <h1>{{ data.department.name }}</h1>
      <p>{{ data.department.summary }}</p>
    </header>
    <article class="portal-page__body" v-html="data.department.description_html" />
    <section class="portal-page__doctors">
      <h2>Doctors in this department</h2>
      <div class="portal-page__doctor-grid">
        <DoctorCard
          v-for="doc in data.doctors"
          :key="doc.user_id"
          :doctor="doc"
          @click="router.push(`/portal/doctors/${doc.user_id}`)"
        />
      </div>
    </section>
  </main>
  <div v-else-if="loading" class="portal-page__loading">Loading…</div>
  <div v-else-if="error" class="portal-page__error">{{ error }}</div>
</template>

<style scoped>
.portal-page { max-width: 880px; margin: 0 auto; padding: 32px 24px 64px; }
.back { background: none; border: 0; color: #4f73ea; padding: 0; cursor: pointer; font-size: 14px; }
.portal-page__hero h1 { margin: 12px 0 4px; font-size: 32px; color: #1f2f4e; }
.portal-page__hero p { margin: 0 0 32px; color: #6f7894; }
.portal-page__body :deep(img) { max-width: 100%; height: auto; border-radius: 10px; }
.portal-page__body :deep(h2), .portal-page__body :deep(h3) { margin-top: 24px; }
.portal-page__doctors h2 { margin: 40px 0 16px; font-size: 22px; }
.portal-page__doctor-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.portal-page__loading, .portal-page__error { padding: 60px 0; text-align: center; color: #6f7894; }
</style>
