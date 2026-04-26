<script setup lang="ts">
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
    title="Confirm Appointment"
    width="520px"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <p style="margin-bottom: 12px; color: var(--el-text-color-secondary);">
      Record preliminary diagnosis as Confirm Info (max 500 chars).
    </p>
    <ElInput
      :model-value="confirmInfo"
      type="textarea"
      :rows="4"
      maxlength="500"
      show-word-limit
      placeholder="Enter preliminary diagnosis..."
      @update:model-value="(value) => emit('update:confirmInfo', value || '')"
    />
    <template #footer>
      <ElButton @click="emit('update:modelValue', false)">Cancel</ElButton>
      <ElButton
        type="primary"
        :disabled="!confirmInfo.trim() || confirmInfoTooLong"
        @click="emit('submit')"
      >
        Submit Confirm
      </ElButton>
    </template>
  </ElDialog>
</template>
