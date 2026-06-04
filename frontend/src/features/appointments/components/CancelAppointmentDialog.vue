<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

defineProps<{
  modelValue: boolean
  message: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: []
  close: []
}>()
</script>

<template>
  <ElDialog
    :model-value="modelValue"
    :title="t('appointments.cancelTitle')"
    width="460px"
    :before-close="() => emit('close')"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <p style="color: var(--el-color-danger);">{{ message }}</p>
    <template #footer>
      <ElButton @click="emit('close')">{{ t('appointments.keepAppointment') }}</ElButton>
      <ElButton type="danger" @click="emit('confirm')">{{ t('appointments.confirmCancel') }}</ElButton>
    </template>
  </ElDialog>
</template>
