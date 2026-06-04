<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  ElAlert,
  ElButton,
  ElCheckbox,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElRadio,
  ElRadioGroup,
  ElSwitch,
  ElTabPane,
  ElTabs,
} from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import httpClient from '@/shared/http'
import RichTextEditor from '@/shared/components/RichTextEditor.vue'
import PublishStatusBadge from '../../components/PublishStatusBadge.vue'
import { adminDepartmentsApi } from '../../api/departments'
import { adminDoctorProfilesApi } from '../../api/doctor-profiles'
import type { AssignmentItem, DepartmentCard, DoctorProfileAdmin } from '../../types'

const { t } = useI18n()
const route = useRoute()
const doctorId = computed(() => Number(route.params.id))

interface DoctorAccount {
  id: number
  username: string
  email: string
  name: string
  phone: string
  is_active: boolean
}

const loading = ref(false)
const loadError = ref(false)
const activeTab = ref<'account' | 'profile'>('account')

// Account tab state
const account = ref<DoctorAccount | null>(null)
const accountFormRef = ref<FormInstance>()
const accountForm = reactive({
  name: '',
  email: '',
  phone: '',
  is_active: true,
  password: '',
})
const accountRules: FormRules = {
  name: [{ required: true, message: () => t('doctorDetail.nameRequired'), trigger: 'blur' }],
  email: [{ required: true, message: () => t('doctorDetail.emailRequired'), trigger: 'blur' }],
  phone: [{ required: true, message: () => t('doctorDetail.phoneRequired'), trigger: 'blur' }],
}
const savingAccount = ref(false)

// Public profile tab state
const profile = ref<DoctorProfileAdmin | null>(null)
const departments = ref<DepartmentCard[]>([])
const assignments = reactive<Record<number, { selected: boolean }>>({})
const primaryId = ref<number | null>(null)
const initialAssignmentKey = ref('')
const savingProfile = ref(false)
const reviewActing = ref(false)

const displayName = computed(() => account.value?.name?.trim() || profile.value?.name || '-')

const selectedDepartments = computed(() =>
  departments.value.filter((d) => assignments[d.id]?.selected),
)

function assignmentKey() {
  return selectedDepartments.value
    .map((d) => `${d.id}:${primaryId.value === d.id ? 1 : 0}`)
    .sort()
    .join(',')
}

const loadAccount = async () => {
  const res = await httpClient.get<DoctorAccount[]>('/api/auth/doctors/')
  const found = res.data.find((d) => d.id === doctorId.value)
  if (!found) {
    throw new Error('not-found')
  }
  account.value = found
  accountForm.name = found.name
  accountForm.email = found.email
  accountForm.phone = found.phone
  accountForm.is_active = found.is_active
  accountForm.password = ''
}

const loadProfile = async () => {
  const [p, depts] = await Promise.all([
    adminDoctorProfilesApi.detail(doctorId.value),
    adminDepartmentsApi.list(),
  ])
  profile.value = p
  departments.value = depts
  primaryId.value = null
  for (const d of depts) assignments[d.id] = { selected: false }
  for (const link of p.departments) {
    const match = depts.find((x) => x.slug === link.slug)
    if (match) {
      assignments[match.id].selected = true
      if (link.is_primary) primaryId.value = match.id
    }
  }
  initialAssignmentKey.value = assignmentKey()
}

const loadAll = async () => {
  loading.value = true
  loadError.value = false
  try {
    await Promise.all([loadAccount(), loadProfile()])
  } catch {
    loadError.value = true
  } finally {
    loading.value = false
  }
}

const saveAccount = async () => {
  const valid = await accountFormRef.value?.validate().catch(() => false)
  if (!valid) return
  savingAccount.value = true
  try {
    const payload: Record<string, unknown> = {
      name: accountForm.name.trim(),
      email: accountForm.email.trim(),
      phone: accountForm.phone.trim(),
      is_active: accountForm.is_active,
    }
    if (accountForm.password.trim()) payload.password = accountForm.password.trim()
    await httpClient.patch(`/api/auth/doctors/${doctorId.value}/`, payload)
    accountForm.password = ''
    ElMessage.success(t('doctorDetail.accountSaved'))
    await loadAccount()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('doctorDetail.accountSaveFailed'))
  } finally {
    savingAccount.value = false
  }
}

const saveProfile = async () => {
  if (!profile.value) return
  savingProfile.value = true
  try {
    await adminDoctorProfilesApi.update(doctorId.value, {
      title: profile.value.title,
      specialty: profile.value.specialty,
      bio_draft_html: profile.value.bio_draft_html,
      bio_published_html: profile.value.bio_published_html,
    })
    if (assignmentKey() !== initialAssignmentKey.value) {
      const items: AssignmentItem[] = selectedDepartments.value.map((d) => ({
        department_id: d.id,
        is_primary: d.id === primaryId.value,
      }))
      await adminDoctorProfilesApi.setDepartments(doctorId.value, items)
    }
    ElMessage.success(t('doctorDetail.profileSaved'))
    await loadProfile()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('doctorDetail.profileSaveFailed'))
  } finally {
    savingProfile.value = false
  }
}

const approve = async () => {
  reviewActing.value = true
  try {
    await adminDoctorProfilesApi.approve(doctorId.value)
    ElMessage.success(t('doctorDetail.reviewApproved'))
    await loadProfile()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('doctorDetail.reviewActionFailed'))
  } finally {
    reviewActing.value = false
  }
}

const reject = async () => {
  let note: string
  try {
    const result = await ElMessageBox.prompt(
      t('doctorDetail.reviewReasonForRejection'),
      t('doctorDetail.reviewReject'),
      {
        inputValidator: (v) => Boolean(v && v.trim().length),
        inputErrorMessage: t('doctorDetail.reviewReasonRequired'),
      },
    )
    note = (result as { value: string }).value
  } catch {
    return // cancelled
  }
  reviewActing.value = true
  try {
    await adminDoctorProfilesApi.reject(doctorId.value, note)
    ElMessage.success(t('doctorDetail.reviewRejected'))
    await loadProfile()
  } catch (error: any) {
    ElMessage.error(error.response?.data?.detail || t('doctorDetail.reviewActionFailed'))
  } finally {
    reviewActing.value = false
  }
}

const fmtTime = (s?: string | null) => (s ? new Date(s).toLocaleString() : '')

onMounted(loadAll)
</script>

<template>
  <div class="page doctor-detail" v-loading="loading">
    <ElAlert
      v-if="loadError"
      :title="t('doctorDetail.loadFailed')"
      type="error"
      show-icon
      :closable="false"
    />

    <template v-else-if="!loading">
      <header class="doctor-detail__header page-header">
        <h2>{{ displayName }}</h2>
        <PublishStatusBadge
          v-if="profile"
          :status="profile.draft_status"
          :published="profile.is_published"
        />
      </header>

      <ElTabs v-model="activeTab">
        <!-- Account tab -->
        <ElTabPane :label="t('doctorDetail.tabAccount')" name="account">
          <ElForm
            ref="accountFormRef"
            :model="accountForm"
            :rules="accountRules"
            label-position="top"
            class="detail-form"
          >
            <ElFormItem :label="t('doctorDetail.fieldName')" prop="name">
              <ElInput v-model="accountForm.name" :placeholder="t('doctorDetail.placeholderName')" />
            </ElFormItem>
            <ElFormItem :label="t('doctorDetail.fieldEmail')" prop="email">
              <ElInput v-model="accountForm.email" :placeholder="t('doctorDetail.placeholderEmail')" />
            </ElFormItem>
            <ElFormItem :label="t('doctorDetail.fieldPhone')" prop="phone">
              <ElInput v-model="accountForm.phone" :placeholder="t('doctorDetail.placeholderPhone')" />
            </ElFormItem>
            <ElFormItem :label="t('doctorDetail.fieldActive')">
              <ElSwitch v-model="accountForm.is_active" />
            </ElFormItem>
            <ElFormItem :label="t('doctorDetail.fieldPassword')">
              <ElInput
                v-model="accountForm.password"
                type="password"
                show-password
                :placeholder="t('doctorDetail.placeholderResetPassword')"
              />
            </ElFormItem>
            <div class="detail-form__actions">
              <ElButton type="primary" :loading="savingAccount" @click="saveAccount">
                {{ t('common.save') }}
              </ElButton>
            </div>
          </ElForm>
        </ElTabPane>

        <!-- Public profile tab -->
        <ElTabPane :label="t('doctorDetail.tabProfile')" name="profile">
          <div
            v-if="profile && profile.draft_status === 'pending'"
            class="review-card"
          >
            <div class="review-card__head">
              <strong>{{ t('doctorDetail.reviewTitle') }}</strong>
              <span v-if="profile.draft_submitted_at" class="review-card__meta">
                {{ t('doctorDetail.reviewSubmittedAt') }}: {{ fmtTime(profile.draft_submitted_at) }}
              </span>
            </div>
            <div class="review-card__label">{{ t('doctorDetail.reviewDraftPreview') }}</div>
            <div class="review-card__preview" v-html="profile.bio_draft_html" />
            <div class="review-card__actions">
              <ElButton type="success" :loading="reviewActing" @click="approve">
                {{ t('doctorDetail.reviewApprove') }}
              </ElButton>
              <ElButton type="danger" :loading="reviewActing" @click="reject">
                {{ t('doctorDetail.reviewReject') }}
              </ElButton>
            </div>
          </div>

          <ElForm v-if="profile" label-position="top" class="detail-form">
            <ElFormItem :label="t('doctorDetail.fieldTitle')">
              <ElInput v-model="profile.title" :placeholder="t('doctorDetail.titlePlaceholder')" />
            </ElFormItem>
            <ElFormItem :label="t('doctorDetail.fieldSpecialty')">
              <ElInput
                v-model="profile.specialty"
                :placeholder="t('doctorDetail.specialtyPlaceholder')"
              />
            </ElFormItem>
            <ElFormItem :label="t('doctorDetail.fieldDepartments')">
              <div class="dept-grid">
                <ElCheckbox
                  v-for="d in departments"
                  :key="d.id"
                  v-model="assignments[d.id].selected"
                >
                  {{ d.name }}
                </ElCheckbox>
              </div>
            </ElFormItem>
            <ElFormItem :label="t('doctorDetail.fieldPrimaryDepartment')">
              <ElRadioGroup v-model="primaryId">
                <ElRadio v-for="d in selectedDepartments" :key="d.id" :label="d.id">
                  {{ d.name }}
                </ElRadio>
              </ElRadioGroup>
            </ElFormItem>
            <ElFormItem :label="t('doctorDetail.fieldBio')">
              <RichTextEditor v-model="profile.bio_draft_html" />
            </ElFormItem>
            <div class="detail-form__actions">
              <ElButton type="primary" :loading="savingProfile" @click="saveProfile">
                {{ t('common.save') }}
              </ElButton>
            </div>
          </ElForm>
        </ElTabPane>
      </ElTabs>
    </template>
  </div>
</template>

<style scoped>
.doctor-detail {
  padding: 24px;
  max-width: 960px;
}
.doctor-detail__header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}
.doctor-detail__header h2 {
  margin: 0;
  font-size: 22px;
}
.detail-form {
  max-width: 720px;
}
.detail-form__actions {
  margin-top: 16px;
}
.dept-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 6px;
}
.review-card {
  border: 1px solid #f0c97a;
  background: #fffaf0;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 20px;
}
.review-card__head {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 10px;
}
.review-card__meta {
  font-size: 12px;
  color: #8a6d3b;
}
.review-card__label {
  font-size: 13px;
  color: #5b6478;
  margin-bottom: 6px;
}
.review-card__preview {
  max-height: 200px;
  overflow: auto;
  font-size: 13px;
  color: #2e3a59;
  border: 1px dashed #d0d7e2;
  background: #fff;
  padding: 10px;
  border-radius: 6px;
  margin-bottom: 12px;
}
.review-card__preview :deep(img) {
  max-width: 120px;
}
.review-card__actions {
  display: flex;
  gap: 10px;
}
</style>
