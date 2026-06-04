<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { AppointmentStatus } from '../types'

const { t } = useI18n()

defineProps<{
  search: string
  status: 'all' | AppointmentStatus
}>()

const emit = defineEmits<{
  'update:search': [value: string]
  'update:status': [value: 'all' | AppointmentStatus]
  search: []
  reset: []
}>()
</script>

<template>
  <section class="filters filters-inline appointments-filters">
    <ElInput
      :model-value="search"
      :placeholder="t('appointments.searchPlaceholder')"
      clearable
      style="width: 280px;"
      @update:model-value="(value) => emit('update:search', value || '')"
      @keyup.enter="emit('search')"
    />
    <ElSelect
      :model-value="status"
      style="width: 160px;"
      @update:model-value="(value) => emit('update:status', value)"
    >
      <ElOption :label="t('appointments.allStatus')" value="all" />
      <ElOption :label="t('status.pending')" value="pending" />
      <ElOption :label="t('status.confirmed')" value="confirmed" />
      <ElOption :label="t('status.completed')" value="completed" />
      <ElOption :label="t('status.cancelled')" value="cancelled" />
    </ElSelect>
    <ElButton type="primary" @click="emit('search')">{{ t('common.search') }}</ElButton>
    <ElButton :disabled="!search && status === 'all'" @click="emit('reset')">{{ t('common.reset') }}</ElButton>
  </section>
</template>
