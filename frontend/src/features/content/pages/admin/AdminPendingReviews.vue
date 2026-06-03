<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElButton, ElMessage, ElMessageBox, ElTable, ElTableColumn } from 'element-plus'
import { adminDoctorProfilesApi } from '../../api/doctor-profiles'
import type { DoctorProfileAdmin } from '../../types'

const { t } = useI18n()
const items = ref<DoctorProfileAdmin[]>([])
const loading = ref(false)

const load = async () => {
  loading.value = true
  try {
    items.value = await adminDoctorProfilesApi.pendingReviews()
  } finally {
    loading.value = false
  }
}

const approve = async (userId: number) => {
  await adminDoctorProfilesApi.approve(userId)
  ElMessage.success(t('admin.approved'))
  await load()
}

const reject = async (userId: number) => {
  const result = await ElMessageBox.prompt(t('admin.reasonForRejection'), t('admin.reject'), {
    inputValidator: (v) => Boolean(v && v.trim().length),
    inputErrorMessage: t('admin.reasonRequired'),
  })
  const { value } = result as { value: string; action: string }
  await adminDoctorProfilesApi.reject(userId, value)
  ElMessage.success(t('admin.rejected'))
  await load()
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header"><h1>{{ t('admin.pendingReviews') }}</h1></header>
    <ElTable v-loading="loading" :data="items">
      <ElTableColumn prop="name" :label="t('admin.doctor')" />
      <ElTableColumn :label="t('admin.draftPreview')">
        <template #default="{ row }">
          <div class="draft-preview" v-html="row.bio_draft_html" />
        </template>
      </ElTableColumn>
      <ElTableColumn prop="draft_submitted_at" :label="t('admin.submitted')" width="200" />
      <ElTableColumn :label="t('common.actions')" width="220">
        <template #default="{ row }">
          <ElButton size="small" type="success" @click="approve(row.user_id)">{{ t('admin.approve') }}</ElButton>
          <ElButton size="small" type="danger" @click="reject(row.user_id)">{{ t('admin.reject') }}</ElButton>
        </template>
      </ElTableColumn>
    </ElTable>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; }
.admin-page__header h1 { margin: 0 0 18px; font-size: 22px; }
.draft-preview { max-height: 120px; overflow: auto; font-size: 13px; color: #2e3a59; border: 1px dashed #d0d7e2; padding: 8px; border-radius: 6px; }
.draft-preview :deep(img) { max-width: 80px; }
</style>
