<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElButton, ElMessage, ElMessageBox, ElTable, ElTableColumn, ElTag } from 'element-plus'
import { adminDepartmentsApi } from '../../api/departments'
import type { DepartmentCard } from '../../types'

const { t } = useI18n()
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
  await ElMessageBox.confirm(t('admin.deleteDepartmentConfirm'), t('common.confirm'), { type: 'warning' })
  await adminDepartmentsApi.remove(id)
  ElMessage.success(t('admin.deleted'))
  await load()
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <h1>{{ t('admin.departments') }}</h1>
      <ElButton type="primary" @click="router.push('/admin/departments/new')">{{ t('admin.newDepartment') }}</ElButton>
    </header>
    <ElTable v-loading="loading" :data="items">
      <ElTableColumn prop="name" :label="t('admin.name')" />
      <ElTableColumn prop="slug" :label="t('admin.slug')" />
      <ElTableColumn prop="summary" :label="t('admin.summary')" />
      <ElTableColumn prop="display_order" :label="t('admin.order')" width="100" />
      <ElTableColumn :label="t('admin.status')" width="120">
        <template #default="{ row }">
          <ElTag :type="row.is_published ? 'success' : 'info'">
            {{ row.is_published ? t('admin.published') : t('admin.draft') }}
          </ElTag>
        </template>
      </ElTableColumn>
      <ElTableColumn :label="t('common.actions')" width="200">
        <template #default="{ row }">
          <ElButton size="small" @click="router.push(`/admin/departments/${row.id}`)">{{ t('common.edit') }}</ElButton>
          <ElButton size="small" type="danger" @click="removeDept(row.id)">{{ t('common.delete') }}</ElButton>
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
