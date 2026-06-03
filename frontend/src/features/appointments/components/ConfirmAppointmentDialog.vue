<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  modelValue: boolean
  confirmInfo: string
  confirmInfoTooLong: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:confirmInfo': [value: string]
  submit: []
}>()
</script>

<template>
  <ElDialog
    :model-value="modelValue"
    :title="t('appointments.confirmTitle')"
    width="520px"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <p style="margin-bottom: 12px; color: var(--el-text-color-secondary);">
      {{ t('appointments.confirmInfoHint') }}
    </p>
    <ElInput
      :model-value="confirmInfo"
      type="textarea"
      :rows="4"
      maxlength="500"
      show-word-limit
      :placeholder="t('appointments.confirmInfoPlaceholder')"
      @update:model-value="(value) => emit('update:confirmInfo', value || '')"
    />
    <template #footer>
      <ElButton @click="emit('update:modelValue', false)">{{ t('common.cancel') }}</ElButton>
      <ElButton
        type="primary"
        :disabled="!confirmInfo.trim() || confirmInfoTooLong"
        @click="emit('submit')"
      >
        {{ t('appointments.submitConfirm') }}
      </ElButton>
    </template>
  </ElDialog>
</template>
