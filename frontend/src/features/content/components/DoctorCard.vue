<script setup lang="ts">
import type { DoctorPortalCard } from '../types'

defineProps<{ doctor: DoctorPortalCard }>()
</script>

<template>
  <article class="doctor-card">
    <div class="doctor-card__avatar">
      <img v-if="doctor.cover_image_url" :src="doctor.cover_image_url" :alt="doctor.name" />
      <span v-else>{{ doctor.name.charAt(0) }}</span>
    </div>
    <div class="doctor-card__body">
      <h4 class="doctor-card__name">{{ doctor.name }}</h4>
      <p class="doctor-card__title">{{ doctor.title }}</p>
      <p class="doctor-card__specialty">{{ doctor.specialty }}</p>
      <div class="doctor-card__tags">
        <span v-for="d in doctor.departments" :key="d.slug" :class="{ primary: d.is_primary }">
          {{ d.name }}
        </span>
      </div>
    </div>
  </article>
</template>

<style scoped>
.doctor-card { display: flex; gap: 14px; padding: 14px; border-radius: 12px; background: #fff; box-shadow: 0 4px 14px rgba(38, 53, 88, 0.08); }
.doctor-card__avatar { width: 64px; height: 64px; border-radius: 50%; background: #e8eefa; overflow: hidden; display: flex; align-items: center; justify-content: center; font-size: 22px; color: #4f73ea; font-weight: 700; }
.doctor-card__avatar img { width: 100%; height: 100%; object-fit: cover; }
.doctor-card__name { margin: 0; font-size: 15px; color: #1f2f4e; }
.doctor-card__title { margin: 2px 0 0; font-size: 12px; color: #6f7894; }
.doctor-card__specialty { margin: 4px 0 0; font-size: 13px; color: #2e3a59; }
.doctor-card__tags { margin-top: 8px; display: flex; flex-wrap: wrap; gap: 4px; }
.doctor-card__tags span { font-size: 11px; padding: 2px 8px; border-radius: 999px; background: #eef3fb; color: #4f73ea; }
.doctor-card__tags span.primary { background: #4f73ea; color: #fff; }
</style>
