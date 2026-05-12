<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElAlert, ElButton, ElForm, ElFormItem, ElInput, ElMessage } from 'element-plus'
import RichTextEditor from '@/shared/components/RichTextEditor.vue'
import PublishStatusBadge from '../../components/PublishStatusBadge.vue'
import { doctorSelfApi } from '../../api/doctor-profiles'
import { useDraftReview } from '../../composables/useDraftReview'
import { useAuthStore } from '@/features/auth'
import type { DoctorProfileSelf } from '../../types'

const authStore = useAuthStore()
const profile = ref<DoctorProfileSelf | null>(null)
const saving = ref(false)
const submitting = ref(false)
const activeTab = ref<'draft' | 'published'>('draft')

const { isLocked, canSubmit, wasRejected, wasApproved } = useDraftReview(profile)

const displayName = computed(
  () => authStore.user?.name || authStore.user?.username || 'Doctor',
)
const initial = computed(() => displayName.value.charAt(0).toUpperCase())

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
    const msg =
      (e as { response?: { status?: number } }).response?.status === 409
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
  <section v-if="profile" class="my-profile">
    <header class="my-profile__header">
      <div class="my-profile__identity">
        <span class="my-profile__avatar">
          <img
            v-if="authStore.user?.avatar_data"
            :src="authStore.user.avatar_data"
            :alt="displayName"
          />
          <template v-else>{{ initial }}</template>
        </span>
        <div class="my-profile__title-block">
          <h1>My public profile</h1>
          <p class="my-profile__subtitle">{{ displayName }}</p>
        </div>
        <PublishStatusBadge
          class="my-profile__badge"
          :status="profile.draft_status"
          :published="profile.is_published"
        />
      </div>
      <div class="my-profile__actions">
        <ElButton
          :disabled="isLocked"
          :loading="saving"
          type="primary"
          @click="save"
        >
          Save draft
        </ElButton>
        <ElButton
          :disabled="!canSubmit"
          :loading="submitting"
          type="success"
          @click="submitForReview"
        >
          Submit for review
        </ElButton>
      </div>
    </header>

    <nav class="my-profile__tabs" role="tablist">
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'draft'"
        :class="{ active: activeTab === 'draft' }"
        @click="activeTab = 'draft'"
      >
        Draft <span class="tab-hint">(editing)</span>
      </button>
      <button
        type="button"
        role="tab"
        :aria-selected="activeTab === 'published'"
        :class="{ active: activeTab === 'published' }"
        @click="activeTab = 'published'"
      >
        Published <span class="tab-hint">(read-only)</span>
      </button>
    </nav>

    <ElAlert
      v-if="isLocked"
      type="warning"
      :closable="false"
      class="status-note"
      title="Awaiting review"
    >
      Your draft is waiting for admin approval. Editing is locked until it is approved or rejected.
    </ElAlert>
    <ElAlert
      v-else-if="wasRejected"
      type="error"
      :closable="false"
      class="status-note"
      title="Last submission rejected"
    >
      {{ profile.draft_review_note || '(no reason provided)' }}
    </ElAlert>
    <ElAlert
      v-else-if="wasApproved"
      type="success"
      :closable="false"
      class="status-note"
      title="Latest version is live"
    >
      Editing now will mark this as a new draft.
    </ElAlert>

    <div v-show="activeTab === 'draft'" class="my-profile__panel">
      <ElForm label-position="top" class="my-profile__form">
        <div class="my-profile__row">
          <ElFormItem label="Title" class="my-profile__field">
            <ElInput
              v-model="profile.title"
              :disabled="isLocked"
              placeholder="e.g. Senior Consultant"
            />
          </ElFormItem>
          <ElFormItem label="Specialty" class="my-profile__field">
            <ElInput
              v-model="profile.specialty"
              :disabled="isLocked"
              placeholder="e.g. Cardiology"
            />
          </ElFormItem>
        </div>
        <ElFormItem label="Bio">
          <RichTextEditor v-model="profile.bio_draft_html" :disabled="isLocked" />
        </ElFormItem>
      </ElForm>
    </div>

    <div v-show="activeTab === 'published'" class="my-profile__panel">
      <div class="my-profile__published-grid">
        <div class="my-profile__published-meta">
          <div>
            <label>Title</label>
            <p>{{ profile.title || '—' }}</p>
          </div>
          <div>
            <label>Specialty</label>
            <p>{{ profile.specialty || '—' }}</p>
          </div>
          <div v-if="profile.departments?.length">
            <label>Departments</label>
            <p>
              <span
                v-for="d in profile.departments"
                :key="d.slug"
                class="dept-tag"
                :class="{ primary: d.is_primary }"
              >
                {{ d.name }}
              </span>
            </p>
          </div>
        </div>
        <div class="my-profile__published-bio">
          <label>Currently published bio</label>
          <div
            v-if="profile.bio_published_html"
            class="published-html"
            v-html="profile.bio_published_html"
          />
          <div v-else class="published-empty">
            Nothing published yet. Save a draft and submit for review to publish.
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.my-profile {
  padding: 24px clamp(24px, 4vw, 48px) 48px;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

.my-profile__header {
  position: sticky;
  top: 0;
  z-index: 5;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 12px 0 16px;
  border-bottom: 1px solid #e7eaf2;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.my-profile__identity {
  display: flex;
  align-items: center;
  gap: 14px;
}

.my-profile__avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #4f73ea;
  color: #fff;
  font-weight: 700;
  font-size: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.my-profile__avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.my-profile__title-block h1 {
  margin: 0;
  font-size: 20px;
  color: #1f2f4e;
  line-height: 1.2;
}

.my-profile__subtitle {
  margin: 2px 0 0;
  font-size: 13px;
  color: #6f7894;
}

.my-profile__badge {
  margin-left: 8px;
}

.my-profile__actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.my-profile__tabs {
  display: flex;
  gap: 4px;
  border-bottom: 1px solid #e7eaf2;
  margin-bottom: 18px;
}

.my-profile__tabs button {
  background: none;
  border: 0;
  padding: 10px 16px;
  font-size: 14px;
  color: #6f7894;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.15s, border-color 0.15s;
}

.my-profile__tabs button:hover {
  color: #2e3a59;
}

.my-profile__tabs button.active {
  color: #4f73ea;
  border-bottom-color: #4f73ea;
  font-weight: 600;
}

.tab-hint {
  font-size: 12px;
  font-weight: 400;
  color: #95a3c2;
  margin-left: 2px;
}

.status-note {
  margin-bottom: 16px;
}

.my-profile__panel {
  background: #fff;
  border: 1px solid #e7eaf2;
  border-radius: 14px;
  padding: 24px clamp(20px, 3vw, 28px);
}

.my-profile__form :deep(.el-form-item) {
  margin-bottom: 18px;
}

.my-profile__row {
  display: grid;
  grid-template-columns: minmax(240px, 360px) minmax(240px, 360px);
  gap: 20px;
}

.my-profile__row :deep(.el-form-item) {
  margin-bottom: 0;
}

.my-profile__published-grid {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 24px;
}

.my-profile__published-meta > div {
  margin-bottom: 18px;
}

.my-profile__published-meta label,
.my-profile__published-bio label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.4px;
  text-transform: uppercase;
  color: #95a3c2;
  margin-bottom: 6px;
}

.my-profile__published-meta p {
  margin: 0;
  font-size: 14px;
  color: #1f2f4e;
}

.dept-tag {
  display: inline-flex;
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 999px;
  background: #eef3fb;
  color: #4f73ea;
  margin-right: 4px;
  margin-bottom: 4px;
}

.dept-tag.primary {
  background: #4f73ea;
  color: #fff;
}

.published-html {
  font-size: 14px;
  line-height: 1.6;
  color: #2e3a59;
}

.published-html :deep(img) {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
}

.published-html :deep(h1),
.published-html :deep(h2),
.published-html :deep(h3) {
  margin-top: 18px;
}

.published-empty {
  padding: 24px;
  background: #f7f9fc;
  border: 1px dashed #d0d7e2;
  border-radius: 10px;
  text-align: center;
  color: #95a3c2;
  font-size: 13px;
}

@media (max-width: 720px) {
  .my-profile__header {
    flex-direction: column;
    align-items: flex-start;
  }
  .my-profile__row {
    grid-template-columns: 1fr;
  }
  .my-profile__published-grid {
    grid-template-columns: 1fr;
  }
}
</style>
