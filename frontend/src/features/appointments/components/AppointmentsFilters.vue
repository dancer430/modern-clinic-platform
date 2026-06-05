<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { AppointmentStatus, UserOption } from '../types'

const { t } = useI18n()

defineProps<{
  doctorId: number | null
  patientId: number | null
  doctors: UserOption[]
  patients: UserOption[]
  status: 'all' | AppointmentStatus
  date: string
}>()

const emit = defineEmits<{
  'update:doctorId': [value: number | null]
  'update:patientId': [value: number | null]
  'update:status': [value: 'all' | AppointmentStatus]
  'update:date': [value: string]
  search: []
  reset: []
  today: []
}>()

const optionLabel = (user: UserOption) => user.name || user.username
</script>

<template>
  <section class="filters filters-inline appointments-filters">
    <ElSelect
      :model-value="doctorId"
      filterable
      clearable
      :placeholder="t('appointments.filterDoctor')"
      style="width: 200px;"
      @update:model-value="(value) => emit('update:doctorId', value ?? null)"
    >
      <ElOption
        v-for="doctor in doctors"
        :key="doctor.id"
        :label="optionLabel(doctor)"
        :value="doctor.id"
      />
    </ElSelect>
    <ElSelect
      :model-value="patientId"
      filterable
      clearable
      :placeholder="t('appointments.filterPatient')"
      style="width: 200px;"
      @update:model-value="(value) => emit('update:patientId', value ?? null)"
    >
      <ElOption
        v-for="patient in patients"
        :key="patient.id"
        :label="optionLabel(patient)"
        :value="patient.id"
      />
    </ElSelect>
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
    <ElDatePicker
      :model-value="date"
      type="date"
      value-format="YYYY-MM-DD"
      :placeholder="t('appointments.dateFilter')"
      style="width: 160px;"
      @update:model-value="(value) => emit('update:date', value || '')"
    />
    <ElButton @click="emit('today')">{{ t('appointments.todayFilter') }}</ElButton>
    <ElButton type="primary" @click="emit('search')">{{ t('common.search') }}</ElButton>
    <ElButton
      :disabled="!doctorId && !patientId && status === 'all' && !date"
      @click="emit('reset')"
    >
      {{ t('common.reset') }}
    </ElButton>
  </section>
</template>
