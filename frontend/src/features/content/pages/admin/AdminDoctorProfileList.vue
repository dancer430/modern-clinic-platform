<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElTable, ElTableColumn } from 'element-plus'
import PublishStatusBadge from '../../components/PublishStatusBadge.vue'
import { adminDoctorProfilesApi } from '../../api/doctor-profiles'
import type { DoctorProfileAdmin } from '../../types'

const router = useRouter()
const items = ref<DoctorProfileAdmin[]>([])
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    items.value = await adminDoctorProfilesApi.list()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <h1>Doctor profiles</h1>
    </header>
    <ElTable v-loading="loading" :data="items">
      <ElTableColumn prop="name" label="Name" />
      <ElTableColumn prop="title" label="Title" />
      <ElTableColumn prop="specialty" label="Specialty" />
      <ElTableColumn label="Departments">
        <template #default="{ row }">
          <span v-for="d in row.departments" :key="d.slug" class="dept-tag" :class="{ primary: d.is_primary }">{{ d.name }}</span>
        </template>
      </ElTableColumn>
      <ElTableColumn label="Status" width="160">
        <template #default="{ row }">
          <PublishStatusBadge :status="row.draft_status" :published="row.is_published" />
        </template>
      </ElTableColumn>
      <ElTableColumn label="Actions" width="120">
        <template #default="{ row }">
          <ElButton size="small" @click="router.push(`/admin/doctor-profiles/${row.user_id}`)">Edit</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; }
.admin-page__header h1 { margin: 0 0 18px; font-size: 22px; }
.dept-tag { display: inline-flex; font-size: 12px; padding: 2px 8px; border-radius: 999px; background: #eef3fb; color: #4f73ea; margin-right: 4px; }
.dept-tag.primary { background: #4f73ea; color: #fff; }
</style>
