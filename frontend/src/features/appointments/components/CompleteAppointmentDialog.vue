<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { CompleteAppointmentForm } from '../types'

const { t } = useI18n()

defineProps<{
  modelValue: boolean
  completeForm: CompleteAppointmentForm
  completeSubmitAttempted: boolean
  completeFormInvalid: boolean
  completeUploaderDragging: boolean
  showSqliteAttachmentHint: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:completeSubmitAttempted': [value: boolean]
  'update:completeUploaderDragging': [value: boolean]
  submit: []
  attachmentChange: [event: Event]
  attachmentDrop: [event: DragEvent]
  removeAttachment: [index: number]
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)

const closeDialog = () => {
  emit('update:modelValue', false)
  emit('update:completeSubmitAttempted', false)
}

const openAttachmentPicker = () => {
  fileInputRef.value?.click()
}
</script>

<template>
  <ElDialog
    :model-value="modelValue"
    :title="t('appointments.completeTitle')"
    width="620px"
    :before-close="closeDialog"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <p style="margin-bottom: 12px; color: var(--el-text-color-secondary);">
      {{ t('appointments.completeHint') }}
    </p>
    <ElForm label-position="top">
      <ElFormItem :label="t('appointments.diagnosisResult')" required>
        <ElInput
          v-model="completeForm.diagnosisResult"
          type="textarea"
          :rows="3"
          :placeholder="t('appointments.diagnosisResultPlaceholder')"
          :class="{ 'is-error': completeSubmitAttempted && !completeForm.diagnosisResult.trim() }"
        />
      </ElFormItem>
      <ElFormItem :label="t('appointments.treatmentPlan')" required>
        <ElInput
          v-model="completeForm.treatmentPlan"
          type="textarea"
          :rows="3"
          :placeholder="t('appointments.treatmentPlanPlaceholder')"
          :class="{ 'is-error': completeSubmitAttempted && !completeForm.treatmentPlan.trim() }"
        />
      </ElFormItem>
      <ElFormItem :label="t('appointments.medicalAdvice')">
        <ElInput
          v-model="completeForm.medicalAdvice"
          type="textarea"
          :rows="3"
          :placeholder="t('appointments.medicalAdvicePlaceholder')"
        />
      </ElFormItem>
      <ElFormItem :label="t('appointments.attachmentsImage')">
        <div class="complete-attachment-area">
          <div
            class="file-uploader"
            :class="{ dragging: completeUploaderDragging }"
            role="button"
            tabindex="0"
            @click="openAttachmentPicker"
            @keydown.enter.prevent="openAttachmentPicker"
            @dragover.prevent="emit('update:completeUploaderDragging', true)"
            @dragleave.prevent="emit('update:completeUploaderDragging', false)"
            @drop.prevent="emit('attachmentDrop', $event)"
          >
            <input
              ref="fileInputRef"
              type="file"
              accept="image/*"
              multiple
              class="hidden-file-input"
              @change="emit('attachmentChange', $event)"
            />
            <span class="file-uploader-icon">&#x2B06;</span>
            <div>
              <p class="file-uploader-title">{{ t('appointments.uploadAttachments') }}</p>
              <p class="file-uploader-subtitle">{{ t('appointments.uploadAttachmentsHint') }}</p>
            </div>
          </div>
          <p v-if="showSqliteAttachmentHint" style="margin: 4px 0 0; color: var(--el-text-color-secondary); font-size: 12px;">
            {{ t('appointments.sqliteAttachmentHint') }}
          </p>
          <ul v-if="completeForm.attachments.length > 0" class="complete-attachment-list">
            <li v-for="(item, index) in completeForm.attachments" :key="`${item.file_name}-${index}`">
              <span>{{ item.file_name }} &middot; {{ item.compressed_size }}KB</span>
              <ElButton text type="danger" size="small" @click="emit('removeAttachment', index)">{{ t('appointments.removeAttachment') }}</ElButton>
            </li>
          </ul>
        </div>
      </ElFormItem>
      <ElFormItem>
        <ElCheckbox v-model="completeForm.createNextAppointment">
          {{ t('appointments.createNextAppointment') }}
        </ElCheckbox>
      </ElFormItem>
    </ElForm>
    <template #footer>
      <ElButton @click="closeDialog">{{ t('common.cancel') }}</ElButton>
      <ElButton type="primary" :disabled="completeFormInvalid" @click="emit('submit')">{{ t('appointments.submitComplete') }}</ElButton>
    </template>
  </ElDialog>
</template>

<style scoped>
.complete-attachment-area {
  width: 100%;
}
.file-uploader {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 2px dashed var(--el-border-color, #dcdfe6);
  border-radius: 6px;
  cursor: pointer;
  transition: border-color 0.2s;
}
.file-uploader:hover,
.file-uploader.dragging {
  border-color: var(--el-color-primary);
}
.file-uploader-icon {
  font-size: 24px;
}
.file-uploader-title {
  font-weight: 500;
  margin: 0;
}
.file-uploader-subtitle {
  color: var(--el-text-color-secondary);
  font-size: 12px;
  margin: 2px 0 0;
}
.hidden-file-input {
  display: none;
}
.complete-attachment-list {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
.complete-attachment-list li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}
</style>
