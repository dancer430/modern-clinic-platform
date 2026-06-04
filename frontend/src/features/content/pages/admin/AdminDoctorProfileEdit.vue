<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElButton, ElCheckbox, ElForm, ElFormItem, ElInput, ElMessage, ElRadio, ElRadioGroup, ElSwitch } from 'element-plus'
import RichTextEditor from '@/shared/components/RichTextEditor.vue'
import PublishStatusBadge from '../../components/PublishStatusBadge.vue'
import { adminDepartmentsApi } from '../../api/departments'
import { adminDoctorProfilesApi } from '../../api/doctor-profiles'
import type { AssignmentItem, DepartmentCard, DoctorProfileAdmin } from '../../types'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const userId = computed(() => Number(route.params.userId))

const profile = ref<DoctorProfileAdmin | null>(null)
const departments = ref<DepartmentCard[]>([])
const assignments = reactive<Record<number, { selected: boolean; is_primary: boolean }>>({})
const primaryId = ref<number | null>(null)
const saving = ref(false)

const loadAll = async () => {
  const [p, depts] = await Promise.all([
    adminDoctorProfilesApi.detail(userId.value),
    adminDepartmentsApi.list(),
  ])
  profile.value = p
  departments.value = depts
  for (const d of depts) assignments[d.id] = { selected: false, is_primary: false }
  for (const link of p.departments) {
    const match = depts.find((x) => x.slug === link.slug)
    if (match) {
      assignments[match.id].selected = true
      if (link.is_primary) {
        assignments[match.id].is_primary = true
        primaryId.value = match.id
      }
    }
  }
}

const save = async () => {
  if (!profile.value) return
  saving.value = true
  try {
    await adminDoctorProfilesApi.update(userId.value, {
      title: profile.value.title,
      specialty: profile.value.specialty,
      bio_draft_html: profile.value.bio_draft_html,
      bio_published_html: profile.value.bio_published_html,
      is_published: profile.value.is_published,
    })
    const items: AssignmentItem[] = Object.entries(assignments)
      .filter(([, v]) => v.selected)
      .map(([id]) => ({
        department_id: Number(id),
        is_primary: Number(id) === primaryId.value,
      }))
    await adminDoctorProfilesApi.setDepartments(userId.value, items)
    ElMessage.success(t('admin.saved'))
    await loadAll()
  } finally {
    saving.value = false
  }
}

onMounted(loadAll)
</script>

<template>
  <section class="admin-page" v-if="profile">
    <header class="admin-page__header">
      <h1>{{ profile.name }} ({{ profile.username }})</h1>
      <PublishStatusBadge :status="profile.draft_status" :published="profile.is_published" />
      <ElButton @click="router.push('/admin/doctor-profiles')">{{ t('common.back') }}</ElButton>
    </header>
    <ElForm label-position="top" class="admin-form">
      <ElFormItem :label="t('admin.title')"><ElInput v-model="profile.title" /></ElFormItem>
      <ElFormItem :label="t('admin.specialty')"><ElInput v-model="profile.specialty" /></ElFormItem>
      <ElFormItem :label="t('admin.publishedBioLive')"><RichTextEditor v-model="profile.bio_published_html" /></ElFormItem>
      <ElFormItem :label="t('admin.draftBio')"><RichTextEditor v-model="profile.bio_draft_html" /></ElFormItem>
      <ElFormItem :label="t('admin.published')"><ElSwitch v-model="profile.is_published" /></ElFormItem>
      <ElFormItem :label="t('admin.departmentsColumn')">
        <div class="dept-grid">
          <div v-for="d in departments" :key="d.id" class="dept-row">
            <ElCheckbox v-model="assignments[d.id].selected">{{ d.name }}</ElCheckbox>
          </div>
        </div>
      </ElFormItem>
      <ElFormItem :label="t('admin.primaryDepartment')">
        <ElRadioGroup v-model="primaryId">
          <ElRadio v-for="d in departments.filter((x) => assignments[x.id].selected)" :key="d.id" :label="d.id">{{ d.name }}</ElRadio>
        </ElRadioGroup>
      </ElFormItem>
      <div class="admin-form__actions">
        <ElButton type="primary" :loading="saving" @click="save">{{ t('common.save') }}</ElButton>
      </div>
    </ElForm>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; max-width: 960px; }
.admin-page__header { display: flex; align-items: center; gap: 12px; margin-bottom: 18px; }
.admin-page__header h1 { margin: 0; font-size: 22px; }
.admin-form__actions { margin-top: 16px; }
.dept-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 6px; }
</style>
