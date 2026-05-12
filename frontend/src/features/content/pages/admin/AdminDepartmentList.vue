<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElButton, ElMessage, ElMessageBox, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { adminDepartmentsApi } from '../../api/departments'
import type { DepartmentCard } from '../../types'

const router = useRouter()
const items = ref<DepartmentCard[]>([])
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    items.value = await adminDepartmentsApi.list()
  } finally {
    loading.value = false
  }
}

const removeDept = async (id: number) => {
  await ElMessageBox.confirm('Delete this department?', 'Confirm', { type: 'warning' })
  await adminDepartmentsApi.remove(id)
  ElMessage.success('Deleted')
  await load()
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <h1>Departments</h1>
      <ElButton type="primary" @click="router.push('/admin/departments/new')">New department</ElButton>
    </header>
    <ElTable v-loading="loading" :data="items">
      <ElTableColumn prop="name" label="Name" />
      <ElTableColumn prop="slug" label="Slug" />
      <ElTableColumn prop="summary" label="Summary" />
      <ElTableColumn prop="display_order" label="Order" width="100" />
      <ElTableColumn label="Status" width="120">
        <template #default="{ row }">
          <ElTag :type="row.is_published ? 'success' : 'info'">
            {{ row.is_published ? 'Published' : 'Draft' }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn label="Actions" width="200">
        <template #default="{ row }">
          <ElButton size="small" @click="router.push(`/admin/departments/${row.id}`)">Edit</ElButton>
          <ElButton size="small" type="danger" @click="removeDept(row.id)">Delete</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; }
.admin-page__header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.admin-page__header h1 { margin: 0; font-size: 22px; }
</style>
