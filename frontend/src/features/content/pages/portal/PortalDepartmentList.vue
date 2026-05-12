<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import DepartmentCard from '../../components/DepartmentCard.vue'
import { usePortalDepartments } from '../../composables/usePortalDepartments'

const { items, loading, error, load } = usePortalDepartments()
const router = useRouter()

onMounted(() => load())
</script>

<template>
  <main class="portal-page">
    <header class="portal-page__header">
      <h1>Departments</h1>
      <p>Browse our clinical departments and find the right team.</p>
    </header>
    <div v-if="loading" class="portal-page__loading">Loading…</div>
    <div v-else-if="error" class="portal-page__error">{{ error }}</div>
    <div v-else class="portal-page__grid">
      <DepartmentCard
        v-for="d in items"
        :key="d.id"
        :department="d"
        @click="router.push(`/portal/departments/${d.slug}`)"
      />
    </div>
  </main>
</template>

<style scoped>
.portal-page { max-width: 1120px; margin: 0 auto; padding: 48px 24px; }
.portal-page__header h1 { margin: 0; font-size: 32px; color: #1f2f4e; }
.portal-page__header p { margin: 8px 0 28px; color: #6f7894; }
.portal-page__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 22px; }
.portal-page__loading, .portal-page__error { padding: 60px 0; text-align: center; color: #6f7894; }
</style>
