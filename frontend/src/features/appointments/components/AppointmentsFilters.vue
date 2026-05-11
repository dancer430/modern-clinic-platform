<script setup lang="ts">
import type { AppointmentStatus } from '../types'

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
      placeholder="Search patient/doctor/reason"
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
      <ElOption label="All status" value="all" />
      <ElOption label="pending" value="pending" />
      <ElOption label="confirmed" value="confirmed" />
      <ElOption label="completed" value="completed" />
      <ElOption label="cancelled" value="cancelled" />
    </ElSelect>
    <ElButton type="primary" @click="emit('search')">Search</ElButton>
    <ElButton :disabled="!search && status === 'all'" @click="emit('reset')">Reset</ElButton>
  </section>
</template>
