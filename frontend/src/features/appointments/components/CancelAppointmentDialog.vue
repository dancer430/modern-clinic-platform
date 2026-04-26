<script setup lang="ts">
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
    title="Cancel Appointment"
    width="460px"
    :before-close="() => emit('close')"
    @update:model-value="(value) => emit('update:modelValue', value)"
  >
    <p style="color: var(--el-color-danger);">{{ message }}</p>
    <template #footer>
      <ElButton @click="emit('close')">Keep Appointment</ElButton>
      <ElButton type="danger" @click="emit('confirm')">Confirm Cancel</ElButton>
    </template>
  </ElDialog>
</template>
