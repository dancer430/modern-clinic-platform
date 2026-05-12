<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput, ElMessage } from 'element-plus'
import RichTextEditor from '@/shared/components/RichTextEditor.vue'
import PublishStatusBadge from '../../components/PublishStatusBadge.vue'
import { doctorSelfApi } from '../../api/doctor-profiles'
import { useDraftReview } from '../../composables/useDraftReview'
import type { DoctorProfileSelf } from '../../types'

const profile = ref<DoctorProfileSelf | null>(null)
const saving = ref(false)
const submitting = ref(false)

const { isLocked, canSubmit, wasRejected, wasApproved } = useDraftReview(profile)

const load = async () => {
  profile.value = await doctorSelfApi.me()
}

const save = async () => {
  if (!profile.value) return
  saving.value = true
  try {
    profile.value = await doctorSelfApi.save({
      title: profile.value.title,
      specialty: profile.value.specialty,
      bio_draft_html: profile.value.bio_draft_html,
    })
    ElMessage.success('Saved')
  } catch (e: unknown) {
    const msg = (e as { response?: { status?: number } }).response?.status === 409
      ? 'Editing is locked while review is pending.'
      : 'Save failed'
    ElMessage.error(msg)
  } finally {
    saving.value = false
  }
}

const submitForReview = async () => {
  submitting.value = true
  try {
    profile.value = await doctorSelfApi.submitReview()
    ElMessage.success('Submitted for review')
  } catch {
    ElMessage.error('Submit failed')
  } finally {
    submitting.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="admin-page" v-if="profile">
    <header class="admin-page__header">
      <h1>My public profile</h1>
      <PublishStatusBadge :status="profile.draft_status" :published="profile.is_published" />
    </header>

    <ElAlert v-if="isLocked" type="warning" :closable="false" class="status-note">
      Your draft is awaiting review. Editing is locked until an admin approves or rejects it.
    </ElAlert>
    <ElAlert v-else-if="wasRejected" type="error" :closable="false" class="status-note">
      Last submission was rejected: {{ profile.draft_review_note || '(no note)' }}.
    </ElAlert>
    <ElAlert v-else-if="wasApproved" type="success" :closable="false" class="status-note">
      Latest version is published. Editing now will reset status to draft.
    </ElAlert>

    <ElForm label-position="top" class="admin-form">
      <ElFormItem label="Title"><ElInput v-model="profile.title" :disabled="isLocked" /></ElFormItem>
      <ElFormItem label="Specialty"><ElInput v-model="profile.specialty" :disabled="isLocked" /></ElFormItem>
      <ElFormItem label="Bio (draft — visible after admin approves)">
        <RichTextEditor v-model="profile.bio_draft_html" :disabled="isLocked" />
      </ElFormItem>
      <ElFormItem label="Currently published bio">
        <div class="published-preview" v-html="profile.bio_published_html || '<em>(nothing published yet)</em>'" />
      </ElFormItem>
      <div class="admin-form__actions">
        <ElButton :disabled="isLocked" :loading="saving" type="primary" @click="save">Save draft</ElButton>
        <ElButton :disabled="!canSubmit" :loading="submitting" type="success" @click="submitForReview">Submit for review</ElButton>
      </div>
    </ElForm>
  </section>
</template>

<style scoped>
.admin-page { padding: 24px; max-width: 880px; }
.admin-page__header { display: flex; gap: 12px; align-items: center; margin-bottom: 12px; }
.admin-page__header h1 { margin: 0; font-size: 22px; }
.status-note { margin-bottom: 16px; }
.published-preview { padding: 12px; background: #f7f9fc; border-radius: 8px; min-height: 80px; }
.published-preview :deep(img) { max-width: 200px; }
.admin-form__actions { margin-top: 16px; display: flex; gap: 12px; }
</style>
