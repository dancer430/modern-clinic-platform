<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElButton, ElForm, ElFormItem, ElInput, ElInputNumber, ElMessage, ElSwitch, ElUpload } from 'element-plus'
import type { UploadRawFile } from 'element-plus'
import RichTextEditor from '@/shared/components/RichTextEditor.vue'
import { adminDepartmentsApi } from '../../api/departments'
import { uploadMedia } from '../../api/media-upload'
import type { DepartmentAdminInput } from '../../types'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const isNew = computed(() => route.params.id === 'new')
const id = computed(() => (isNew.value ? null : Number(route.params.id)))

const form = reactive<DepartmentAdminInput & { cover_image_url: string | null }>({
  name: '', slug: '', summary: '', description_html: '',
  display_order: 0, is_published: false, cover_image_url: null,
})
const saving = ref(false)

const load = async () => {
  if (id.value == null) return
  const data = await adminDepartmentsApi.detail(id.value)
  Object.assign(form, data)
}

const handleCoverUpload = async (raw: UploadRawFile) => {
  const url = await uploadMedia(raw as File)
  form.cover_image_url = url
  ElMessage.success(t('admin.uploaded'))
  return false
}

const save = async () => {
  saving.value = true
  try {
    if (isNew.value) {
      const created = await adminDepartmentsApi.create(form)
      ElMessage.success(t('admin.created'))
      router.replace(`/admin/departments/${created.id}`)
    } else if (id.value != null) {
      await adminDepartmentsApi.update(id.value, form)
      ElMessage.success(t('admin.saved'))
    }
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="admin-page">
    <header class="admin-page__header">
      <h1>{{ isNew ? t('admin.newDepartment') : t('admin.editDepartment') }}</h1>
      <ElButton @click="router.push('/admin/departments')">{{ t('common.back') }}</ElButton>
    </header>
    <ElForm :model="form" label-position="top" class="admin-form">
      <ElFormItem :label="t('admin.name')"><ElInput v-model="form.name" /></ElFormItem>
      <ElFormItem :label="t('admin.slug')"><ElInput v-model="form.slug" /></ElFormItem>
      <ElFormItem :label="t('admin.summary')"><ElInput v-model="form.summary" /></ElFormItem>
      <ElFormItem :label="t('admin.description')">
        <RichTextEditor v-model="form.description_html" />
      </ElFormItem>
      <ElFormItem :label="t('admin.displayOrder')"><ElInputNumber v-model="form.display_order" :min="0" /></ElFormItem>
      <ElFormItem :label="t('admin.published')"><ElSwitch v-model="form.is_published" /></ElFormItem>
      <ElFormItem :label="t('admin.coverImage')">
        <ElUpload :before-upload="handleCoverUpload" :show-file-list="false" accept="image/*">
          <ElButton>{{ t('admin.uploadCover') }}</ElButton>
        </ElUpload>
        <img v-if="form.cover_image_url" :src="form.cover_image_url" class="admin-form__cover" />
      </ElFormItem>
      <div class="admin-form__actions">
        <ElButton type="primary" :loading="saving" @click="save">{{ t('common.save') }}</ElButton>
      </div>
    </ElForm>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; max-width: 880px; }
.admin-page__header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.admin-form { display: flex; flex-direction: column; gap: 4px; }
.admin-form__cover { display: block; margin-top: 12px; max-width: 240px; border-radius: 8px; }
.admin-form__actions { margin-top: 16px; }
</style>
