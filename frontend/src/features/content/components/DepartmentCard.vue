<script setup lang="ts">
import type { DepartmentCard as Card } from '../types'

defineProps<{ department: Card }>()
</script>

<template>
  <article class="dept-card">
    <div class="dept-card__cover" :style="department.cover_image_url ? `background-image:url(${department.cover_image_url})` : ''">
      <span v-if="!department.cover_image_url" class="dept-card__placeholder">{{ department.name.charAt(0) }}</span>
    </div>
    <div class="dept-card__body">
      <h3 class="dept-card__title">{{ department.name }}</h3>
      <p class="dept-card__summary">{{ department.summary }}</p>
    </div>
  </article>
</template>

<style scoped>
.dept-card {
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 14px;
  overflow: hidden;
  box-shadow: 0 6px 18px rgba(38, 53, 88, 0.08);
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.dept-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(38, 53, 88, 0.14);
}
.dept-card__cover {
  height: 140px;
  background: linear-gradient(135deg, #4f73ea, #2e57db);
  background-size: cover;
  background-position: center;
  display: flex;
  align-items: center;
  justify-content: center;
}
.dept-card__placeholder {
  font-size: 48px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 700;
}
.dept-card__body {
  padding: 16px 18px;
}
.dept-card__title {
  margin: 0 0 6px;
  font-size: 16px;
  color: #1f2f4e;
}
.dept-card__summary {
  margin: 0;
  font-size: 13px;
  color: #6f7894;
  line-height: 1.5;
}
</style>
