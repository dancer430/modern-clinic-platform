<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { portalDoctorsApi } from '../../api/doctor-profiles'
import type { DoctorPortalDetail } from '../../types'

const route = useRoute()
const router = useRouter()
const doctor = ref<DoctorPortalDetail | null>(null)
const loading = ref(false)
const error = ref<string | null>(null)

const load = async () => {
  loading.value = true
  try {
    doctor.value = await portalDoctorsApi.detail(Number(route.params.userId))
    if (doctor.value?.name) {
      document.title = `${doctor.value.name} – Doctors`
    }
  } catch (e) {
    error.value = (e as Error).message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="portal-page" v-if="!loading && doctor">
    <button class="back" @click="router.push('/portal/doctors')">← All doctors</button>
    <header class="portal-page__hero">
      <div class="portal-page__avatar">
        <img v-if="doctor.cover_image_url" :src="doctor.cover_image_url" :alt="doctor.name" />
        <span v-else>{{ doctor.name.charAt(0) }}</span>
      </div>
      <div>
        <h1>{{ doctor.name }}</h1>
        <p>{{ doctor.title }} · {{ doctor.specialty }}</p>
        <div class="portal-page__tags">
          <span v-for="d in doctor.departments" :key="d.slug" :class="{ primary: d.is_primary }">{{ d.name }}</span>
        </div>
      </div>
    </header>
    <article class="portal-page__body" v-html="doctor.bio_published_html" />
  </main>
  <div v-else-if="loading" class="portal-page__loading">Loading…</div>
  <div v-else-if="error" class="portal-page__error">{{ error }}</div>
</template>

<style scoped>
.portal-page { max-width: 880px; margin: 0 auto; padding: 32px 24px 64px; }
.back { background: none; border: 0; color: #4f73ea; padding: 0; cursor: pointer; font-size: 14px; }
.portal-page__hero { display: flex; gap: 20px; align-items: center; margin: 16px 0 28px; }
.portal-page__avatar { width: 96px; height: 96px; border-radius: 50%; overflow: hidden; background: #e8eefa; display: flex; align-items: center; justify-content: center; font-size: 36px; color: #4f73ea; font-weight: 700; }
.portal-page__avatar img { width: 100%; height: 100%; object-fit: cover; }
.portal-page__hero h1 { margin: 0; }
.portal-page__hero p { margin: 4px 0; color: #6f7894; }
.portal-page__tags { margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap; }
.portal-page__tags span { font-size: 12px; padding: 2px 10px; border-radius: 999px; background: #eef3fb; color: #4f73ea; }
.portal-page__tags span.primary { background: #4f73ea; color: #fff; }
.portal-page__body :deep(img) { max-width: 100%; height: auto; border-radius: 10px; }
.portal-page__loading, .portal-page__error { padding: 60px 0; text-align: center; color: #6f7894; }
</style>
